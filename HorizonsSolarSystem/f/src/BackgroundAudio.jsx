import React from 'react';

const BackgroundAudio = ({ isPlaying, setIsPlaying, volume, setVolume, showControls = false }) => {
  const toggleAudio = () => {
    setIsPlaying(!isPlaying);
  };

  const handleVolumeChange = (e) => {
    setVolume(parseFloat(e.target.value));
  };

  if (!showControls) return null;

  return (
    <div className="background-audio-player" style={{
      position: 'fixed',
      top: '10px',
      right: '10px',
      zIndex: 1000,
      background: 'rgba(0, 0, 0, 0.7)',
      padding: '10px',
      borderRadius: '5px'
    }}>
      <button onClick={toggleAudio} style={{ marginRight: '10px' }}>
        {isPlaying ? '🔇 Mute' : '🔊 Unmute'}
      </button>
      <input
        type="range"
        min="0"
        max="1"
        step="0.01"
        value={volume}
        onChange={handleVolumeChange}
        style={{ width: '100px', verticalAlign: 'middle' }}
      />
    </div>
  );
};

export default BackgroundAudio;