import { useState, useEffect, useRef } from 'react'
import './App.css'
import './CrtEffect.css' 
import TerminalEmulator from './TerminalEmulator'

function App() {
  const [loading, setLoading] = useState(true)
  const [isPlaying, setIsPlaying] = useState(true)
  const [volume, setVolume] = useState(0.5)
  const [userInteracted, setUserInteracted] = useState(false)
  const audioRef = useRef(null)

  useEffect(() => {
    setTimeout(() => {
      setLoading(false)
    }, 2000)

    const handleInteraction = () => {
      setUserInteracted(true)
      document.removeEventListener('click', handleInteraction)
    }
    document.addEventListener('click', handleInteraction)

    return () => {
      document.removeEventListener('click', handleInteraction)
    }
  }, [])

  useEffect(() => {
    if (userInteracted && audioRef.current) {
      audioRef.current.volume = volume
      audioRef.current.play().catch(error => {
        console.error("Audio playback failed:", error);
        setIsPlaying(false);
      });
    }
  }, [userInteracted, volume])

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.volume = volume
      if (isPlaying && userInteracted) {
        audioRef.current.play().catch(console.error);
      } else {
        audioRef.current.pause();
      }
    }
  }, [isPlaying, volume, userInteracted])

  const audioProps = { 
    isPlaying, 
    setIsPlaying, 
    volume, 
    setVolume,
    audioRef 
  }

  return (
    <>
      <audio ref={audioRef} src="/background-music.mp3" loop />
      {!userInteracted ? (
        <div 
          style={{
            position: 'fixed', 
            top: 0, 
            left: 0, 
            width: '100%', 
            height: '100%', 
            background: 'rgba(0,0,0,0.5)', 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center',
            zIndex: 9999
          }}
          onClick={() => setUserInteracted(true)}
        >
          <button className="entrance">
            AUTHENTICATE
          </button>
        </div>
      ) : (
        <div className="terminal-container crt">
          <TerminalEmulator {...audioProps} />
        </div>
      )}
    </>
  )
}

export default App