import React, { useState, useEffect, useMemo, useRef } from 'react';
import BackgroundAudio from './BackgroundAudio';

const CustomChar = ({ char }) => {
  const grid = useMemo(() => {
    return Array(3).fill().map(() => Array(2).fill().map(() => Math.random() < 0.5));
  }, [char]);

  return (
    <div className="custom-char">
      {grid.map((row, rowIndex) => (
        <div key={rowIndex} className="char-row">
          {row.map((cell, cellIndex) => (
            <div
              key={`${rowIndex}-${cellIndex}`}
              className={`char-cell ${cell ? 'active' : ''}`}
            />
          ))}
        </div>
      ))}
    </div>
  );
};

const LoadingOverlay = ({ minDisplayTime = 2000, onPasswordSubmit, isPlaying, setIsPlaying, volume, setVolume }) => {
  const [loading, setLoading] = useState(true);
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [hint, setHint] = useState(null);
  const [showFileUpload, setShowFileUpload] = useState(false);
  const fileInputRef = useRef(null);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLoading(false);
    }, minDisplayTime);

    return () => clearTimeout(timer);
  }, [minDisplayTime]);

  useEffect(() => {
    const fetchHint = async () => {
      try {
        const response = await fetch('/api/get-password-hint/');
        const data = await response.json();
        if (data.hint) {
          setHint(data.hint);
        }
      } catch (error) {
        console.error('Error fetching hint:', error);
      }
    };

    const intervalId = setInterval(fetchHint, 1000);

    return () => clearInterval(intervalId);
  }, []);

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch('/api/check-password/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ password }),
      });
      const data = await response.json();
      if (data.status === 'success') {
        setShowFileUpload(true);
        setError('');
        setTimeout(() => {
          fileInputRef.current?.click();
        }, 100);
      } else {
        setError(data.message || 'Access Denied. Please try again.');
      }
    } catch (error) {
      setError('System Error. Please try again.');
    }
  };

  const handleFileChange = async (e) => {
    const file = e.target.files[0];
    if (!file) {
      setError('Please select a file to upload.');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/verify-file/', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (data.status === 'success') {
        onPasswordSubmit();
      } else {
        setError(data.message || 'File verification failed. Please try again.');
      }
    } catch (error) {
      setError('System Error. Please try again.');
    }
  };

  const renderHint = () => {
    if (!hint) return null;

    return (
      <div className="password-hint">
        <div className="qr-code">
          {hint.map((row, rowIndex) => (
            <div key={rowIndex} className="qr-row">
              {row.map((cell, cellIndex) => (
                <div
                  key={`${rowIndex}-${cellIndex}`}
                  className={`qr-cell ${cell ? 'active' : ''}`}
                />
              ))}
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderPassword = () => {
    return (
      <div className="custom-password-display">
        {password.split('').map((char, index) => (
          <CustomChar key={index} char={char} />
        ))}
      </div>
    );
  };

  return (
    <div className="loading-overlay crt">
      <BackgroundAudio 
        isPlaying={isPlaying}
        setIsPlaying={setIsPlaying}
        volume={volume}
        setVolume={setVolume}
        showControls={false}
      />
      {loading ? (
        <div className="loading-message">Initializing Terminal...</div>
      ) : (
        <>
          {renderHint()}
          {!showFileUpload ? (
            <form onSubmit={handlePasswordSubmit} className="password-form">
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter access code"
                className="password-input"
                style={{ position: 'absolute', opacity: 0, pointerEvents: 'none' }}
              />
              <div className="custom-input-wrapper" onClick={() => document.querySelector('.password-input').focus()}>
                {renderPassword()}
              </div>
            </form>
          ) : (
            <div className="file-upload-form">
              <input
                type="file"
                onChange={handleFileChange}
                className="file-input"
                ref={fileInputRef}
                style={{ display: 'none' }}
              />
              <p>File upload initiated.</p>
            </div>
          )}
          {error && <p className="error-message">{error}</p>}
        </>
      )}
    </div>
  );
};

export default LoadingOverlay;