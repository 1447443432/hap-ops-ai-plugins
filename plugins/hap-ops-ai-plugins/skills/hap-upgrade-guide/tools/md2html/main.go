package main

import (
	"bytes"
	_ "embed"
	"flag"
	"fmt"
	"os"
	"regexp"
	"strings"
	"unicode"

	"github.com/PuerkitoBio/goquery"
	"github.com/yuin/goldmark"
	"github.com/yuin/goldmark/extension"
)

//go:embed template.html
var templateHTML string

var numberPrefixRE = regexp.MustCompile(`^\d+[\.\s]+`)
var dateRE = regexp.MustCompile(`\d{4}-\d{2}-\d{2}`)
var languageHintRE = regexp.MustCompile(`(?i)^(bash|sh|shell|yaml|yml|javascript|js|typescript|ts|json|sql|python|py|java|go|rust|dockerfile|docker|text|plaintext|toml|ini|conf|xml|html|css|scss|markdown|md|powershell|ps1|cmd|bat|makefile|nginx|properties|groovy|kotlin|scala|swift|c|cpp|csharp|cs|ruby|rb|php|perl|lua|r|dart|elixir|erlang|haskell|clojure|lisp|fortran|matlab|zig|v|svelte)$`)
var targetDateLabelRE = regexp.MustCompile(`目标版本发布日期`)
var codeBlockRE = regexp.MustCompile(`(?s)(<pre><code(?:\s+class="language-([^"]*)")?>)(.+?)(</code></pre>)`)

func main() {
	inputFile := flag.String("input", "", "Input Markdown file path")
	outputFile := flag.String("output", "", "Output HTML file path")
	title := flag.String("title", "", "Document title (auto-detected from first h1 if empty)")
	flag.Parse()

	if *inputFile == "" || *outputFile == "" {
		fmt.Fprintln(os.Stderr, "Usage: md2html -input <file.md> -output <file.html> [-title <title>]")
		fmt.Fprintln(os.Stderr, "")
		fmt.Fprintln(os.Stderr, "Converts a HAP Upgrade Guide Markdown file to a single-file HTML document")
		fmt.Fprintln(os.Stderr, "with sidebar TOC, code block copy buttons, and responsive layout.")
		os.Exit(1)
	}

	mdData, err := os.ReadFile(*inputFile)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error reading input file: %v\n", err)
		os.Exit(1)
	}

	result, err := Convert(mdData, *title)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error converting: %v\n", err)
		os.Exit(1)
	}

	if err := os.WriteFile(*outputFile, []byte(result), 0644); err != nil {
		fmt.Fprintf(os.Stderr, "Error writing output file: %v\n", err)
		os.Exit(1)
	}

	fmt.Printf("Generated: %s\n", *outputFile)
}

// Convert converts Markdown content to a full HTML document string.
func Convert(mdData []byte, title string) (string, error) {
	var buf bytes.Buffer
	md := goldmark.New(
		goldmark.WithExtensions(
			extension.GFM,
			extension.DefinitionList,
			extension.TaskList,
		),
	)
	if err := md.Convert(mdData, &buf); err != nil {
		return "", fmt.Errorf("goldmark convert: %w", err)
	}
	bodyHTML := buf.String()

	bodyHTML = processCodeBlocks(bodyHTML)

	processed, tocHTML, err := postProcess(bodyHTML)
	if err != nil {
		return "", fmt.Errorf("post-process: %w", err)
	}

	if title == "" {
		title = extractTitle(processed)
	}

	result := strings.ReplaceAll(templateHTML, "{{TITLE}}", title)
	result = strings.ReplaceAll(result, "{{BODY}}", processed)
	result = strings.ReplaceAll(result, "{{TOC}}", tocHTML)

	return result, nil
}

func processCodeBlocks(html string) string {
	return codeBlockRE.ReplaceAllStringFunc(html, func(match string) string {
		parts := codeBlockRE.FindStringSubmatch(match)
		if len(parts) < 5 {
			return match
		}
		openingTag := parts[1]
		lang := parts[2]
		codeContent := parts[3]
		closingTag := parts[4]

		validLang := ""
		if lang != "" && languageHintRE.MatchString(lang) {
			validLang = strings.ToLower(lang)
		}

		var labelHTML string
		if validLang != "" {
			labelHTML = fmt.Sprintf(`<span class="code-lang-label">%s</span>`, validLang)
		}

		return fmt.Sprintf(
			`<div class="code-block" data-lang="%s">%s<button class="copy-btn">复制</button><pre><code%s%s%s</code></pre></div>`,
			validLang, labelHTML,
			strings.TrimPrefix(openingTag, "<pre><code"),
			codeContent, closingTag,
		)
	})
}

type tocEntry struct {
	Level int
	Text  string
	ID    string
}

// postProcess returns processed body HTML and static TOC HTML.
func postProcess(htmlFragment string) (string, string, error) {
	wrapper := fmt.Sprintf(`<html><head></head><body><div class="content">%s</div></body></html>`, htmlFragment)
	doc, err := goquery.NewDocumentFromReader(strings.NewReader(wrapper))
	if err != nil {
		return "", "", err
	}

	content := doc.Find(".content")

	// 1. Fix heading IDs and collect TOC entries
	var tocEntries []tocEntry

	content.Find("h2, h3, h4, h5").Each(func(i int, s *goquery.Selection) {
		text := s.Text()
		stripped := numberPrefixRE.ReplaceAllString(text, "")
		newID := generateHeadingID(stripped)
		s.SetAttr("id", newID)

		tagName := goquery.NodeName(s)
		level := 2
		if len(tagName) >= 2 {
			level = int(tagName[1] - '0')
		}
		tocEntries = append(tocEntries, tocEntry{Level: level, Text: text, ID: newID})
	})

	// 2. Add class="meta-block" to the first table
	content.Find("table").First().AddClass("meta-block")

	// 3. Mark attention blockquotes
	content.Find("blockquote").Each(func(i int, s *goquery.Selection) {
		if strings.Contains(s.Text(), "⚠️") {
			s.AddClass("attention")
		}
	})

	// 4. Highlight dates in meta-block table rows
	content.Find("table.meta-block tr").Each(func(i int, s *goquery.Selection) {
		cells := s.Find("td")
		if cells.Length() < 2 {
			return
		}
		labelCell := cells.First()
		valueCell := cells.Eq(1)
		labelText := strings.TrimSpace(labelCell.Text())

		if strings.Contains(labelText, "发布日期") || strings.Contains(labelText, "日期") {
			valueHTML, _ := valueCell.Html()
			isTarget := targetDateLabelRE.MatchString(labelText)
			newHTML := dateRE.ReplaceAllStringFunc(valueHTML, func(match string) string {
				if isTarget {
					return fmt.Sprintf(`<span class="date-val date-val-primary">%s</span>`, match)
				}
				return fmt.Sprintf(`<span class="date-val">%s</span>`, match)
			})
			if isTarget && strings.Contains(newHTML, "⚠️") {
				newHTML = strings.ReplaceAll(newHTML, "⚠️", `<span style="color:#cf222e;">⚠️</span>`)
			}
			valueCell.SetHtml(newHTML)
		}
	})

	// 5. Highlight inline dates in body text
	content.Find("p, li, blockquote").Each(func(i int, s *goquery.Selection) {
		if s.Parent().Is("td, th") {
			return
		}
		htmlStr, _ := s.Html()
		newHTML := dateRE.ReplaceAllStringFunc(htmlStr, func(match string) string {
			if strings.Contains(match, `<span`) {
				return match
			}
			return fmt.Sprintf(`<span class="inline-date">%s</span>`, match)
		})
		if newHTML != htmlStr {
			s.SetHtml(newHTML)
		}
	})

	// 6. Generate static TOC HTML
	tocHTML := generateTOC(tocEntries)

	bodyHTML, err := content.Html()
	if err != nil {
		return "", "", err
	}
	// 去掉 goquery 格式化可能引入的前导空白，防止正文开头出现多余空白
	bodyHTML = strings.TrimLeft(bodyHTML, " \t\n\r")

	return bodyHTML, tocHTML, nil
}

// generateTOC builds static TOC HTML from heading entries.
func generateTOC(entries []tocEntry) string {
	if len(entries) == 0 {
		return `<ul class="toc" id="toc"></ul>`
	}

	var b strings.Builder
	b.WriteString(`<ul class="toc" id="toc">`)

	var currentSection *strings.Builder
	var currentChildren *strings.Builder

	for _, e := range entries {
		if e.Level == 2 {
			// Close previous section if open
			if currentSection != nil {
				if currentChildren != nil {
					currentSection.WriteString(currentChildren.String())
					currentSection.WriteString(`</ul></li>`)
				} else {
					currentSection.WriteString(`</li>`)
				}
				b.WriteString(currentSection.String())
			}
			currentSection = &strings.Builder{}
			currentSection.WriteString(`<li class="toc-section">`)
			currentSection.WriteString(`<div class="toc-header">`)
			currentSection.WriteString(`<span class="toc-toggle">▾</span>`)
			currentSection.WriteString(fmt.Sprintf(`<a href="#%s">%s</a>`, e.ID, escapeHTML(e.Text)))
			currentSection.WriteString(`</div>`)
			currentChildren = &strings.Builder{}
			currentChildren.WriteString(`<ul class="toc-children">`)
		} else {
			if currentChildren == nil {
				currentChildren = &strings.Builder{}
				currentChildren.WriteString(`<ul class="toc-children">`)
			}
			className := fmt.Sprintf("toc-item h%d", e.Level)
			currentChildren.WriteString(fmt.Sprintf(
				`<li class="%s"><a href="#%s">%s</a></li>`,
				className, e.ID, escapeHTML(e.Text),
			))
		}
	}

	// Close last section
	if currentSection != nil {
		if currentChildren != nil {
			currentSection.WriteString(currentChildren.String())
			currentSection.WriteString(`</ul></li>`)
		} else {
			currentSection.WriteString(`</li>`)
		}
		b.WriteString(currentSection.String())
	}

	b.WriteString(`</ul>`)
	return b.String()
}

func escapeHTML(s string) string {
	s = strings.ReplaceAll(s, "&", "&amp;")
	s = strings.ReplaceAll(s, "<", "&lt;")
	s = strings.ReplaceAll(s, ">", "&gt;")
	s = strings.ReplaceAll(s, `"`, "&quot;")
	return s
}

func generateHeadingID(text string) string {
	var result strings.Builder
	first := true
	for _, r := range text {
		if r == ' ' || r == '\u3000' {
			if !first {
				result.WriteByte('-')
			}
		} else if unicode.Is(unicode.Han, r) || unicode.IsLetter(r) || unicode.IsDigit(r) {
			result.WriteRune(r)
			first = false
		}
	}
	id := strings.Trim(result.String(), "-")
	if id == "" {
		id = "heading"
	}
	return id
}

func extractTitle(htmlFragment string) string {
	doc, _ := goquery.NewDocumentFromReader(strings.NewReader(htmlFragment))
	if h1 := doc.Find("h1").First(); h1.Length() > 0 {
		return strings.TrimSpace(h1.Text())
	}
	return "HAP 升级指南"
}
