import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import './JobRequirements.css';

function JobRequirements() {
  const [content, setContent] = useState('');
  const [editingContent, setEditingContent] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchRequirements();
  }, []);

  const fetchRequirements = async () => {
    try {
      const response = await fetch('http://localhost:5001/api/job-requirements');
      if (response.ok) {
        const data = await response.json();
        setContent(data.content || '');
        setEditingContent(data.content || '');
      } else {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to load job requirements');
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

  const handleSave = async () => {
    setSaving(true);
    setMessage('');

    try {
      const response = await fetch('http://localhost:5001/api/job-requirements', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ content: editingContent }),
      });

      if (response.ok) {
        setContent(editingContent);
        setIsEditing(false);
        setMessage('Job requirements saved successfully!');
        setTimeout(() => setMessage(''), 3000);
      } else {
        const errorData = await response.json();
        setMessage(`Error: ${errorData.error || 'Failed to save job requirements'}`);
      }
    } catch (err) {
      if (err.message === 'Failed to fetch' || err.name === 'TypeError') {
        setMessage('Error: Cannot connect to backend API. Make sure the backend server is running on port 5001.');
      } else {
        setMessage(`Error: ${err.message}`);
      }
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditingContent(content);
    setIsEditing(false);
    setMessage('');
  };

  if (loading) {
    return <div className="job-requirements">Loading job requirements...</div>;
  }

  if (error) {
    return <div className="job-requirements error">{error}</div>;
  }

  return (
    <div className="job-requirements">
      <div className="header-with-buttons">
        <h2>Job Requirements</h2>
        <div className="button-group">
          {!isEditing ? (
            <button onClick={() => setIsEditing(true)} className="edit-button">
              Edit
            </button>
          ) : (
            <>
              <button onClick={handleSave} className="save-button" disabled={saving}>
                {saving ? 'Saving...' : 'Save'}
              </button>
              <button onClick={handleCancel} className="cancel-button" disabled={saving}>
                Cancel
              </button>
            </>
          )}
        </div>
      </div>
      {message && (
        <div className={`message ${message.includes('Error') ? 'error' : 'success'}`}>
          {message}
        </div>
      )}
      {isEditing ? (
        <textarea
          className="requirements-textarea"
          value={editingContent}
          onChange={(e) => setEditingContent(e.target.value)}
          placeholder="Enter your job requirements in Markdown format..."
        />
      ) : (
        <div className="markdown-content">
          {content ? (
            <ReactMarkdown>{content}</ReactMarkdown>
          ) : (
            <p className="empty-state">No job requirements set. Click Edit to add them.</p>
          )}
        </div>
      )}
    </div>
  );
}

export default JobRequirements;

