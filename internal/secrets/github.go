// Package github provides GitHub integration helpers for authentication and credential management.
package github

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strings"
)

const (
	// DefaultGitHubAPIURL is the base URL for the GitHub API.
	DefaultGitHubAPIURL = "https://api.github.com"
	// GitHubTokenHeader is the HTTP header used for token authentication.
	GitHubTokenHeader = "Authorization"
	// GitHubAPIVersion is the GitHub API version header.
	GitHubAPIVersion = "X-GitHub-Api-Version"
)

// Client provides GitHub API client functionality.
type Client struct {
	baseURL string
	token   string
	http    *http.Client
}

// User represents a GitHub user.
type User struct {
	Login string `json:"login"`
	ID    int    `json:"id"`
	Email string `json:"email"`
	Name  string `json:"name"`
}

// Repository represents a GitHub repository.
type Repository struct {
	Name        string `json:"name"`
	FullName    string `json:"full_name"`
	URL         string `json:"url"`
	Private     bool   `json:"private"`
	Description string `json:"description"`
}

// NewClient creates a new GitHub API client with the given token.
func NewClient(token string) *Client {
	return &Client{
		baseURL: DefaultGitHubAPIURL,
		token:   token,
		http:    &http.Client{},
	}
}

// NewClientWithURL creates a new GitHub API client with custom base URL (useful for GitHub Enterprise).
func NewClientWithURL(token, baseURL string) *Client {
	return &Client{
		baseURL: strings.TrimRight(baseURL, "/"),
		token:   token,
		http:    &http.Client{},
	}
}

// GetAuthenticatedUser retrieves the authenticated user's information.
func (c *Client) GetAuthenticatedUser(ctx context.Context) (*User, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, c.baseURL+"/user", nil)
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}

	body, err := c.doRequest(req)
	if err != nil {
		return nil, err
	}

	var user User
	if err := json.Unmarshal(body, &user); err != nil {
		return nil, fmt.Errorf("parsing user response: %w", err)
	}

	return &user, nil
}

// GetRepository retrieves information about a repository.
func (c *Client) GetRepository(ctx context.Context, owner, repo string) (*Repository, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, 
		fmt.Sprintf("%s/repos/%s/%s", c.baseURL, owner, repo), nil)
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}

	body, err := c.doRequest(req)
	if err != nil {
		return nil, err
	}

	var repository Repository
	if err := json.Unmarshal(body, &repository); err != nil {
		return nil, fmt.Errorf("parsing repository response: %w", err)
	}

	return &repository, nil
}

// ValidateToken checks if the provided token is valid by attempting to fetch user information.
func (c *Client) ValidateToken(ctx context.Context) error {
	_, err := c.GetAuthenticatedUser(ctx)
	return err
}

// doRequest executes an HTTP request with GitHub authentication headers.
func (c *Client) doRequest(req *http.Request) ([]byte, error) {
	if c.token != "" {
		req.Header.Set(GitHubTokenHeader, fmt.Sprintf("Bearer %s", c.token))
	}
	req.Header.Set(GitHubAPIVersion, "2022-11-28")
	req.Header.Set("Accept", "application/vnd.github+json")

	resp, err := c.http.Do(req)
	if err != nil {
		return nil, fmt.Errorf("executing request: %w", err)
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("reading response: %w", err)
	}

	// Check for HTTP errors
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		var errorResp struct {
			Message string `json:"message"`
			Documentation string `json:"documentation_url"`
		}
		_ = json.Unmarshal(body, &errorResp)
		
		if errorResp.Message != "" {
			return nil, fmt.Errorf("GitHub API error: %s (status %d)", errorResp.Message, resp.StatusCode)
		}
		return nil, fmt.Errorf("GitHub API error: status %d", resp.StatusCode)
	}

	return body, nil
}

// TokenFromString parses a token string, removing "Bearer" prefix if present.
func TokenFromString(s string) string {
	s = strings.TrimSpace(s)
	if strings.HasPrefix(strings.ToLower(s), "bearer ") {
		return s[7:]
	}
	return s
}

// ValidateGitHubToken validates a GitHub token format and connectivity.
func ValidateGitHubToken(ctx context.Context, token string) (bool, error) {
	if token == "" {
		return false, nil
	}

	client := NewClient(TokenFromString(token))
	return true, client.ValidateToken(ctx)
}

// Issue represents a GitHub issue
type Issue struct {
	Number int    `json:"number"`
	Title  string `json:"title"`
	State  string `json:"state"`
	Body   string `json:"body"`
	URL    string `json:"html_url"`
	User   struct {
		Login string `json:"login"`
	} `json:"user"`
	CreatedAt string `json:"created_at"`
	UpdatedAt string `json:"updated_at"`
	Labels    []struct {
		Name string `json:"name"`
	} `json:"labels"`
}

// IssueListOptions represents options for listing issues
type IssueListOptions struct {
	State  string // "open", "closed", "all"
	Sort   string // "created", "updated", "comments"
	Order  string // "asc", "desc"
	Labels string // comma-separated label names
	Page   int    // page number (default 1)
	PerPage int   // items per page (default 30, max 100)
}

// ListIssues retrieves a list of issues for a repository.
func (c *Client) ListIssues(ctx context.Context, owner, repo string, opts *IssueListOptions) ([]Issue, error) {
	if opts == nil {
		opts = &IssueListOptions{
			State:   "open",
			PerPage: 30,
		}
	}

	url := fmt.Sprintf("%s/repos/%s/%s/issues?state=%s", c.baseURL, owner, repo, opts.State)
	if opts.Sort != "" {
		url += fmt.Sprintf("&sort=%s", opts.Sort)
	}
	if opts.Order != "" {
		url += fmt.Sprintf("&order=%s", opts.Order)
	}
	if opts.Labels != "" {
		url += fmt.Sprintf("&labels=%s", opts.Labels)
	}
	if opts.PerPage > 0 {
		url += fmt.Sprintf("&per_page=%d", opts.PerPage)
	}
	if opts.Page > 0 {
		url += fmt.Sprintf("&page=%d", opts.Page)
	}

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}

	body, err := c.doRequest(req)
	if err != nil {
		return nil, err
	}

	var issues []Issue
	if err := json.Unmarshal(body, &issues); err != nil {
		return nil, fmt.Errorf("parsing issues response: %w", err)
	}

	return issues, nil
}

// GetIssue retrieves a single issue by number.
func (c *Client) GetIssue(ctx context.Context, owner, repo string, number int) (*Issue, error) {
	url := fmt.Sprintf("%s/repos/%s/%s/issues/%d", c.baseURL, owner, repo, number)
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}

	body, err := c.doRequest(req)
	if err != nil {
		return nil, err
	}

	var issue Issue
	if err := json.Unmarshal(body, &issue); err != nil {
		return nil, fmt.Errorf("parsing issue response: %w", err)
	}

	return &issue, nil
}
