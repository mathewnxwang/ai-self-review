import { useState, useEffect } from 'react';
import './ConfigEditor.css';

function ConfigEditor() {
  const [config, setConfig] = useState({ repo: '', year: '' });
  const [secrets, setSecrets] = useState({ github_username: '', github_token: '' });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingSecrets, setSavingSecrets] = useState(false);
  const [message, setMessage] = useState('');
  const [secretsMessage, setSecretsMessage] = useState('');

  useEffect(() => {
    fetchConfig();
    fetchSecrets();
  }, []);

  const fetchConfig = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/config');
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      } else {
        setMessage('Failed to load config');
      }
    } catch (error) {
      if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
        setMessage('Error: Cannot connect to backend API. Make sure the backend server is running on port 5001.');
      } else {
        setMessage(`Error: ${error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchSecrets = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/secrets');
      if (response.ok) {
        const data = await response.json();
        setSecrets({
          github_username: data.github_username || '',
          github_token: data.has_token ? data.github_token : ''
        });
      }
    } catch (error) {
      // Silently fail - secrets might not exist yet
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');

    try {
      const response = await fetch('http://localhost:5001/api/config', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repo: config.repo,
          year: parseInt(config.year),
        }),
      });

      if (response.ok) {
        setMessage('Config saved successfully!');
        setTimeout(() => setMessage(''), 3000);
      } else {
        const error = await response.json();
        setMessage(`Error: ${error.error || 'Failed to save config'}`);
      }
    } catch (error) {
      if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
        setMessage('Error: Cannot connect to backend API. Make sure the backend server is running on port 5001.');
      } else {
        setMessage(`Error: ${error.message}`);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleSecretsSubmit = async (e) => {
    e.preventDefault();
    setSavingSecrets(true);
    setSecretsMessage('');

    try {
      const response = await fetch('http://localhost:5001/api/secrets', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          github_username: secrets.github_username,
          github_token: secrets.github_token,
        }),
      });

      if (response.ok) {
        setSecretsMessage('Credentials saved successfully!');
        setTimeout(() => setSecretsMessage(''), 3000);
        // Refresh to get masked values
        fetchSecrets();
      } else {
        const error = await response.json();
        setSecretsMessage(`Error: ${error.error || 'Failed to save credentials'}`);
      }
    } catch (error) {
      if (error.message === 'Failed to fetch' || error.name === 'TypeError') {
        setSecretsMessage('Error: Cannot connect to backend API. Make sure the backend server is running on port 5001.');
      } else {
        setSecretsMessage(`Error: ${error.message}`);
      }
    } finally {
      setSavingSecrets(false);
    }
  };

  if (loading) {
    return <div className="config-editor">Loading config...</div>;
  }

  return (
    <div className="config-editor">
      <h2>Configuration</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="repo">Repository:</label>
          <input
            id="repo"
            type="text"
            value={config.repo}
            onChange={(e) => setConfig({ ...config, repo: e.target.value })}
            placeholder="owner/repo"
            required
          />
        </div>
        <div className="form-group">
          <label htmlFor="year">Year:</label>
          <input
            id="year"
            type="number"
            value={config.year}
            onChange={(e) => setConfig({ ...config, year: e.target.value })}
            placeholder="2025"
            required
            min="2000"
            max="2100"
          />
        </div>
        <button type="submit" disabled={saving}>
          {saving ? 'Saving...' : 'Save Config'}
        </button>
        {message && (
          <div className={`message ${message.includes('Error') ? 'error' : 'success'}`}>
            {message}
          </div>
        )}
      </form>

      <h3>GitHub Credentials</h3>
      <form onSubmit={handleSecretsSubmit}>
        <div className="form-group">
          <label htmlFor="github_username">GitHub Username:</label>
          <input
            id="github_username"
            type="text"
            value={secrets.github_username}
            onChange={(e) => setSecrets({ ...secrets, github_username: e.target.value })}
            placeholder="your_username"
          />
        </div>
        <div className="form-group">
          <label htmlFor="github_token">GitHub Personal Access Token:</label>
          <input
            id="github_token"
            type="password"
            value={secrets.github_token}
            onChange={(e) => setSecrets({ ...secrets, github_token: e.target.value })}
            placeholder="ghp_xxxxxxxxxxxx"
          />
          <small className="form-help">
            Your token is stored locally and never shared. Create one at{' '}
            <a href="https://github.com/settings/tokens" target="_blank" rel="noopener noreferrer">
              GitHub Settings
            </a>
          </small>
        </div>
        <button type="submit" disabled={savingSecrets}>
          {savingSecrets ? 'Saving...' : 'Save Credentials'}
        </button>
        {secretsMessage && (
          <div className={`message ${secretsMessage.includes('Error') ? 'error' : 'success'}`}>
            {secretsMessage}
          </div>
        )}
      </form>
    </div>
  );
}

export default ConfigEditor;

