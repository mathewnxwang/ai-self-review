import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './SelfReviewSummary.css';

function SelfReviewSummary() {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchSummary();
  }, []);

  const fetchSummary = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/summary');
      if (response.ok) {
        const data = await response.json();
        setContent(data.content || '');
        setError('');
      } else {
        const errorData = await response.json();
        if (errorData.error && !errorData.error.includes('not found')) {
          setError(errorData.error || 'Failed to load summary');
        } else {
          setContent('');
          setError('');
        }
      }
    } catch (err) {
      if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
        setError('Error: Cannot connect to backend API. Make sure the backend server is running on port 5001.');
      } else {
        setError(`Error: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setMessage('');
    setError('');

    try {
      const response = await fetch('http://localhost:5001/api/generate-summary', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        setMessage('Summary generated successfully! Refreshing...');
        // Wait a moment then refresh the summary
        setTimeout(() => {
          fetchSummary();
          setMessage('');
        }, 1000);
      } else {
        const errorData = await response.json();
        setMessage(`Error: ${errorData.error || 'Failed to generate summary'}`);
        if (errorData.details) {
          console.error('Generation details:', errorData.details);
        }
      }
    } catch (err) {
      if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
        setMessage('Error: Cannot connect to backend API. Make sure the backend server is running on port 5001.');
      } else {
        setMessage(`Error: ${err.message}`);
      }
    } finally {
      setGenerating(false);
    }
  };

  if (loading) {
    return <div className="self-review-summary">Loading self-review summary...</div>;
  }

  if (error) {
    return <div className="self-review-summary error">{error}</div>;
  }

  return (
    <div className="self-review-summary">
      <div className="header-with-buttons">
        <h2>Self-Review Summary</h2>
        <button 
          onClick={handleGenerate} 
          className="generate-button" 
          disabled={generating || loading}
        >
          {generating ? 'Generating...' : 'Generate Summary'}
        </button>
      </div>
      {message && (
        <div className={`message ${message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}
      <div className="markdown-content">
        {content ? (
          <ReactMarkdown>{content}</ReactMarkdown>
        ) : (
          <p className="empty-state">
            No summary available. Click "Generate Summary" to create one.
          </p>
        )}
      </div>
    </div>
  );
}

export default SelfReviewSummary;

