import { useState, useRef } from 'react'
import './index.css'

function App() {
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [dragActive, setDragActive] = useState(false)
  
  const fileInputRef = useRef(null)

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const droppedFile = e.dataTransfer.files[0]
      validateAndSetFile(droppedFile)
    }
  }

  const handleChange = (e) => {
    e.preventDefault()
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0])
    }
  }

  const validateAndSetFile = (selectedFile) => {
    setError(null)
    const validTypes = ['audio/mpeg', 'audio/wav', 'audio/mp3', 'audio/x-wav', 'video/mp4']
    
    if (!validTypes.includes(selectedFile.type) && !selectedFile.name.endsWith('.mp3') && !selectedFile.name.endsWith('.wav') && !selectedFile.name.endsWith('.mp4')) {
      setError("Please upload only .mp3, .wav, or .mp4 files")
      setFile(null)
      return
    }
    setFile(selectedFile)
  }

  const processAudio = async () => {
    if (!file) return
    
    setLoading(true)
    setError(null)
    setResult(null)
    
    const formData = new FormData()
    formData.append('file', file)
    
    try {
      // Assuming the backend is running on localhost:8000
      const response = await fetch('http://localhost:8000/process-audio', {
        method: 'POST',
        body: formData,
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || "Failed to process audio")
      }
      
      const data = await response.json()
      setResult(data)
    } catch (err) {
      console.error(err)
      setError(err.message || "An unexpected error occurred while communicating with the server.")
    } finally {
      setLoading(false)
    }
  }

  const triggerFileInput = () => {
    fileInputRef.current.click()
  }

  return (
    <div className="app-container">
      <h1>Audio Intelligence</h1>
      <p className="subtitle">Convert speech to text and extract key insights instantly using AI.</p>
      
      <div 
        className={`upload-section ${dragActive ? 'drag-active' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input 
          ref={fileInputRef}
          type="file" 
          className="file-input" 
          accept=".mp3,.wav,.mp4" 
          onChange={handleChange}
        />
        
        <div className="file-label" onClick={triggerFileInput}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="17 8 12 3 7 8"></polyline>
            <line x1="12" y1="3" x2="12" y2="15"></line>
          </svg>
          {file ? 'Change File' : 'Browse Files or Drag & Drop'}
        </div>
        
        {file && (
          <div className="file-name">
            Selected: {file.name}
          </div>
        )}
        
        <button 
          className="process-btn" 
          onClick={processAudio} 
          disabled={!file || loading}
        >
          {loading ? 'Processing...' : 'Generate Insights'}
        </button>
      </div>

      {error && (
        <div className="error-message">
          <strong>Error:</strong> {error}
        </div>
      )}

      {loading && (
        <div className="loader-container">
          <div className="loader"></div>
          <div className="loader-text">Analyzing audio... This may take a minute depending on file size.</div>
        </div>
      )}

      {result && (
        <div className="results-section">
          <div className="result-card">
            <div className="card-header">
              <h3>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                  <polyline points="14 2 14 8 20 8"></polyline>
                  <line x1="16" y1="13" x2="8" y2="13"></line>
                  <line x1="16" y1="17" x2="8" y2="17"></line>
                  <polyline points="10 9 9 9 8 9"></polyline>
                </svg>
                AI Summary
              </h3>
            </div>
            <div className="card-body">
              {result.summary}
            </div>
          </div>

          <div className="result-card">
            <div className="card-header">
              <h3>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10"></circle>
                  <line x1="12" y1="16" x2="12" y2="12"></line>
                  <line x1="12" y1="8" x2="12.01" y2="8"></line>
                </svg>
                Key Points
              </h3>
            </div>
            <div className="card-body">
              <ul className="key-points-list">
                {result.key_points && result.key_points.map((point, index) => (
                  <li key={index}>{point}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="result-card">
            <div className="card-header">
              <h3>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2c-1.7 0-3 1.2-3 2.6v6.8c0 1.4 1.3 2.6 3 2.6s3-1.2 3-2.6V4.6C15 3.2 13.7 2 12 2z"></path>
                  <path d="M19 10v1a7 7 0 0 1-14 0v-1"></path>
                  <line x1="12" y1="18" x2="12" y2="22"></line>
                  <line x1="8" y1="22" x2="16" y2="22"></line>
                </svg>
                Full Transcript
              </h3>
            </div>
            <div className="card-body">
              {result.transcript}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
