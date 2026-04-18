package main

import (
"context"
"encoding/csv"
"encoding/json"
"flag"
"fmt"
"log"
"os"
"strconv"
"text/tabwriter"
"time"

"github.com/ollama/ollama/envconfig"
"github.com/ollama/ollama/internal/secrets/github"
)

func main() {
owner    := flag.String("owner", "ollama", "Repository owner")
repo     := flag.String("repo", "ollama", "Repository name")
state    := flag.String("state", "open", "Issue state: open, closed, all")
limit    := flag.Int("limit", 20, "Number of issues per page (max 100)")
sort     := flag.String("sort", "created", "Sort by: created, updated, comments")
order    := flag.String("order", "desc", "Order: asc, desc")
labels   := flag.String("labels", "", "Filter by labels (comma-separated)")
allPages := flag.Bool("all-pages", false, "Fetch all pages of results")
output   := flag.String("output", "table", "Output format: table, json, csv")
outFile  := flag.String("out-file", "", "Write output to file instead of stdout")
watch    := flag.Duration("watch", 0, "Poll interval for watch mode (e.g. 30s). 0 = disabled")
diff     := flag.Bool("diff", false, "In watch mode, only show new/changed issues")
flag.Parse()

token := envconfig.GitHubToken()
if token == "" {
tln(os.Stderr, "Error: OLLAMA_GITHUB_TOKEN not set")
tln(os.Stderr, "Set your token with: export OLLAMA_GITHUB_TOKEN=ghp_xxxxx")
tln(os.Stderr)
tln(os.Stderr, "Get a token at: https://github.com/settings/tokens")
t := github.NewClient(token)
opts := &github.IssueListOptions{
  *sort,
*labels,
!= "" {
!= nil {
g output file: %v", err)
> 0 {
Watch(client, *owner, *repo, opts, *allPages, *output, out, *diff, *watch)

}

ctx := context.Background()
issues, err := fetchIssues(ctx, client, *owner, *repo, opts, *allPages)
if err != nil {
g issues: %v", err)
}

if err := writeOutput(out, issues, *output); err != nil {
g output: %v", err)
}
}

// fetchIssues retrieves issues, optionally paginating through all pages.
func fetchIssues(ctx context.Context, client *github.Client, owner, repo string, opts *github.IssueListOptions, allPages bool) ([]github.Issue, error) {
var all []github.Issue
page := 1
for {
err := client.ListIssues(ctx, owner, repo, &o)
il {
 nil, err
d(all, issues...)
(issues) < opts.PerPage {
 all, nil
}

// diffIssues returns issues that are new or whose UpdatedAt changed compared to prev.
func diffIssues(prev map[int]github.Issue, current []github.Issue) []github.Issue {
var changed []github.Issue
for _, iss := range current {
umber]
|| p.State != iss.State {
ged = append(changed, iss)
 changed
}

// writeOutput writes issues to w in the requested format.
func writeOutput(w *os.File, issues []github.Issue, format string) error {
switch format {
case "json":
c := json.NewEncoder(w)
c.SetIndent("", "  ")
 enc.Encode(issues)

case "csv":
ewWriter(w)
g{"number", "title", "state", "author", "labels", "created_at", "updated_at", "url"})
ge issues {
g, len(iss.Labels))
ge iss.Labels {
ame
g{
v.Itoa(iss.Number),
,
Strings(labels, ";"),
 cw.Error()

default: // table
ewWriter(w, 0, 0, 2, ' ', tabwriter.AlignRight)
tln(tw, "#\tSTATE\tAUTHOR\tUPDATED\tTITLE")
tln(tw, "---\t---\t---\t---\t---")
ge issues {
tf(tw, "%d\t%s\t%s\t%s\t%s\n",
umber,
,
cate(iss.Title, 60),
 tw.Flush()
}
}

// runWatch polls GitHub in a loop and prints new/changed issues.
func runWatch(client *github.Client, owner, repo string, opts *github.IssueListOptions, allPages bool, format string, out *os.File, diffOnly bool, interval time.Duration) {
prev := map[int]github.Issue{}
ticker := time.NewTicker(interval)
defer ticker.Stop()

fmt.Fprintf(os.Stderr, "Watching %s/%s every %s (Ctrl-C to stop)\n", owner, repo, interval)

for {
text.Background()
t, owner, repo, opts, allPages)
il {
tf(os.Stderr, "fetch error: %v\n", err)
diffOnly {
(toShow) > 0 {
ly {
tf(os.Stderr, "[%s] %d changed issue(s)\n", time.Now().Format(time.RFC3339), len(toShow))
Update prev index.
ge issues {
umber] = iss
c truncate(s string, maxLen int) string {
if len(s) <= maxLen {
 s
}
return s[:maxLen-3] + "..."
}

func formatDate(dateStr string) string {
if len(dateStr) >= 10 {
 dateStr[:10]
}
return dateStr
}

func joinStrings(ss []string, sep string) string {
result := ""
for i, s := range ss {
+= sep
 result
}
