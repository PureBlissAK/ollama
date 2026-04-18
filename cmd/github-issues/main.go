package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"text/tabwriter"

	"github.com/ollama/ollama/envconfig"
	"github.com/ollama/ollama/internal/secrets/github"
)

func main() {
	owner := flag.String("owner", "ollama", "Repository owner")
	repo := flag.String("repo", "ollama", "Repository name")
	state := flag.String("state", "open", "Issue state: open, closed, all")
	limit := flag.Int("limit", 20, "Number of issues to display")
	sort := flag.String("sort", "created", "Sort by: created, updated, comments")
	order := flag.String("order", "desc", "Order: asc, desc")
	labels := flag.String("labels", "", "Filter by labels (comma-separated)")
	flag.Parse()

	token := envconfig.GitHubToken()
	if token == "" {
		fmt.Println("Error: OLLAMA_GITHUB_TOKEN not set")
		fmt.Println("Set your token with: export OLLAMA_GITHUB_TOKEN=ghp_xxxxx")
		fmt.Println()
		fmt.Println("Get a token at: https://github.com/settings/tokens")
		os.Exit(1)
	}

	ctx := context.Background()

	fmt.Printf("🔍 Checking GitHub issues for %s/%s (state: %s)...\n", *owner, *repo, *state)
	fmt.Println()

	client := github.NewClient(token)

	opts := &github.IssueListOptions{
		State:   *state,
		Sort:    *sort,
		Order:   *order,
		Labels:  *labels,
		PerPage: *limit,
	}

	issues, err := client.ListIssues(ctx, *owner, *repo, opts)
	if err != nil {
		log.Fatalf("❌ Error fetching issues: %v", err)
	}

	if len(issues) == 0 {
		fmt.Println("✅ No issues found.")
		return
	}

	fmt.Printf("📋 Found %d issues:\n\n", len(issues))

	// Create a table writer
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', tabwriter.AlignRight)
	fmt.Fprintln(w, "#\tTITLE\tSTATE\tAUTHOR\tUPDATED")
	fmt.Fprintln(w, "---\t---\t---\t---\t---")

	for _, issue := range issues {
		fmt.Fprintf(w, "%d\t%s\t%s\t%s\t%s\n",
			issue.Number,
			truncate(issue.Title, 45),
			issue.State,
			issue.User.Login,
			formatDate(issue.UpdatedAt),
		)
	}
	w.Flush()

	fmt.Println()
	fmt.Printf("🌐 View on GitHub: https://github.com/%s/%s/issues?state=%s\n", *owner, *repo, *state)
}

func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}

func formatDate(dateStr string) string {
	if len(dateStr) >= 10 {
		return dateStr[:10]
	}
	return dateStr
}
