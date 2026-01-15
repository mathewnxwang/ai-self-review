import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './App.css';

// Default role requirements template
const DEFAULT_ROLE_REQUIREMENTS = `# Job Requirements

## Ownership & Impact
- Takes ownership of projects and delivers end-to-end
- Makes net positive impact to the business
- Identifies and solves important problems

## Technical Craft
- Writes high-quality, maintainable code
- Improves system reliability and performance
- Makes good technical decisions

## Teamwork & Collaboration
- Helps unblock team members
- Shares knowledge effectively
- Contributes to a positive team culture
`;

function App() {
  // Auth state - simple gate
  const [auth, setAuth] = useState(null);
  const [authError, setAuthError] = useState('');

  // Form state - load from localStorage for convenience
  const [formData, setFormData] = useState(() => {
    const saved = localStorage.getItem('selfReviewFormData');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return {
          repos: parsed.repos || ['newfront-insurance/python-backend'],
          year: parsed.year || 2025,
          github_username: parsed.github_username || '',
          github_token: '',
          role_requirements: parsed.role_requirements || DEFAULT_ROLE_REQUIREMENTS,
        };
      } catch {
        return {
          repos: ['newfront-insurance/python-backend'],
          year: 2025,
          github_username: '',
          github_token: '',
          role_requirements: DEFAULT_ROLE_REQUIREMENTS,
        };
      }
    }
    return {
      repos: ['newfront-insurance/python-backend'],
      year: 2025,
      github_username: '',
      github_token: '',
      role_requirements: DEFAULT_ROLE_REQUIREMENTS,
    };
  });

  const [summary, setSummary] = useState('');
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [repoInput, setRepoInput] = useState('');

  // Save non-sensitive form data to localStorage
  useEffect(() => {
    const dataToSave = {
      ...formData,
      github_token: '', // Don't persist tokens
    };
    localStorage.setItem('selfReviewFormData', JSON.stringify(dataToSave));
  }, [formData.repos, formData.year, formData.github_username, formData.role_requirements]);

  const handleChange = (field) => (e) => {
    setFormData({ ...formData, [field]: e.target.value });
  };

  const handleRepoInputKeyDown = (e) => {
    if (e.key === 'Enter' && repoInput.trim()) {
      e.preventDefault();
      const trimmedRepo = repoInput.trim();
      if (!formData.repos.includes(trimmedRepo)) {
        setFormData({ ...formData, repos: [...formData.repos, trimmedRepo] });
      }
      setRepoInput('');
    } else if (e.key === 'Backspace' && repoInput === '' && formData.repos.length > 0) {
      // Remove last repo if backspace is pressed on empty input
      setFormData({ 
        ...formData, 
        repos: formData.repos.slice(0, -1) 
      });
    }
  };

  const removeRepo = (repoToRemove) => {
    setFormData({ 
      ...formData, 
      repos: formData.repos.filter(repo => repo !== repoToRemove) 
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (formData.repos.length === 0) {
      setError('Please add at least one repository');
      return;
    }
    
    setGenerating(true);
    setError('');
    setSummary('');

    try {
      const response = await fetch('/api/generate-summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Basic ' + btoa(auth.username + ':' + auth.password),
        },
        body: JSON.stringify({
          repos: formData.repos,
          year: parseInt(formData.year),
          github_username: formData.github_username,
          github_token: formData.github_token,
          role_requirements: formData.role_requirements,
        }),
      });

      // Get response text first to debug empty/invalid responses
      const responseText = await response.text();
      console.log('Response status:', response.status);
      console.log('Response text:', responseText);
      
      if (!responseText) {
        setError(`Server returned empty response (status: ${response.status})`);
        return;
      }
      
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseErr) {
        console.error('JSON parse error:', parseErr);
        setError(`Invalid JSON response: ${responseText.substring(0, 200)}`);
        return;
      }

      if (response.ok) {
        setSummary(data.summary);
      } else {
        setError(data.error || 'Failed to generate summary');
      }
    } catch (err) {
      console.error('Request error:', err);
      if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
        setError('Cannot connect to backend. Make sure the server is running.');
      } else {
        setError(err.message);
      }
    } finally {
      setGenerating(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(summary);
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const form = e.target;
    const username = form.username.value;
    const password = form.password.value;
    
    setAuthError('');
    
    // Test credentials against the API
    try {
      const response = await fetch('/api/generate-summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Basic ' + btoa(username + ':' + password),
        },
        body: JSON.stringify({ repos: [], year: 2025, github_username: '', github_token: '', role_requirements: '' }),
      });
      
      if (response.status === 401) {
        setAuthError('Invalid username or password');
        return;
      }
      
      // Credentials work (even if request fails for other reasons)
      setAuth({ username, password });
    } catch (err) {
      setAuthError('Cannot connect to server');
    }
  };

  // Login gate
  if (!auth) {
    return (
      <div className="app">
        <header className="app-header">
          <h1>AI Self-Review Generator</h1>
          <p>Please log in to continue</p>
        </header>
        <main className="app-main">
          <form onSubmit={handleLogin} className="review-form" style={{ maxWidth: '400px', margin: '0 auto' }}>
            <div className="form-section">
              <div className="form-group">
                <label htmlFor="username">Username</label>
                <input id="username" type="text" required autoFocus />
              </div>
              <div className="form-group">
                <label htmlFor="password">Password</label>
                <input id="password" type="password" required />
              </div>
            </div>
            <button type="submit" className="generate-button">Log In</button>
            {authError && <div className="error-message">{authError}</div>}
          </form>
        </main>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Self-Review Generator</h1>
        <p>Generate your performance self-review from merged PRs</p>
      </header>

      <main className="app-main">
        <form onSubmit={handleSubmit} className="review-form">
          <div className="form-section">
            <h2>GitHub Configuration</h2>
            
            <div className="form-row">
              <div className="form-group">
                <label htmlFor="repos">Repositories (owner/repo)</label>
                <div 
                  className="repo-input-container"
                  onClick={() => document.getElementById('repos')?.focus()}
                >
                  {formData.repos.map((repo, index) => (
                    <span key={index} className="repo-chip">
                      {repo}
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          removeRepo(repo);
                        }}
                        className="repo-chip-remove"
                        aria-label={`Remove ${repo}`}
                      >
                        ×
                      </button>
                    </span>
                  ))}
                  <input
                    id="repos"
                    type="text"
                    value={repoInput}
                    onChange={(e) => setRepoInput(e.target.value)}
                    onKeyDown={handleRepoInputKeyDown}
                    placeholder={formData.repos.length === 0 ? "Type repo name and press Enter (e.g., owner/repo)" : "Add another repository..."}
                    className="repo-input"
                  />
                </div>
                <small className="form-hint">Type a repository name and press Enter to add it</small>
              </div>
              
              <div className="form-group">
                <label htmlFor="year">Year</label>
                <input
                  id="year"
                  type="number"
                  value={formData.year}
                  onChange={handleChange('year')}
                  min="2000"
                  max="2100"
                  required
                />
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label htmlFor="github_username">GitHub Username</label>
                <input
                  id="github_username"
                  type="text"
                  value={formData.github_username}
                  onChange={handleChange('github_username')}
                  placeholder="your-username"
                  required
                />
              </div>
              
              <div className="form-group">
                <label htmlFor="github_token">
                  GitHub Personal Access Token
                  <a 
                    href="https://github.com/settings/tokens" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="help-link"
                  >
                    (Create one)
                  </a>
                </label>
                <input
                  id="github_token"
                  type="password"
                  value={formData.github_token}
                  onChange={handleChange('github_token')}
                  placeholder="ghp_xxxxxxxxxxxx"
                  required
                />
              </div>
            </div>
          </div>

          <div className="form-section">
            <h2>Role Requirements</h2>
            <p className="section-description">
              Define the criteria your work will be evaluated against. The AI will align your PR summaries with these requirements.
            </p>
            <div className="form-group">
              <textarea
                id="role_requirements"
                value={formData.role_requirements}
                onChange={handleChange('role_requirements')}
                placeholder="Enter your role requirements in Markdown format..."
                rows={12}
                required
              />
            </div>
          </div>

          <button 
            type="submit" 
            className="generate-button"
            disabled={generating}
          >
            {generating ? (
              <>
                <span className="spinner"></span>
                <span>Generating... (this may take a minute)</span>
              </>
            ) : (
              'Generate Self-Review'
            )}
          </button>

          {error && (
            <div className="error-message">
              {error}
            </div>
          )}
        </form>

        {summary && (
          <div className="summary-section">
            <div className="summary-header">
              <h2>Your Self-Review Summary</h2>
              <button onClick={copyToClipboard} className="copy-button">
                Copy to Clipboard
              </button>
            </div>
            <div className="summary-content">
              <ReactMarkdown
                components={{
                  a: ({ node, ...props }) => (
                    <a {...props} target="_blank" rel="noopener noreferrer" />
                  ),
                }}
              >
                {summary}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>
          Your tokens are never stored on the server. They are only used for this single request.
        </p>
      </footer>
    </div>
  );
}

export default App;
