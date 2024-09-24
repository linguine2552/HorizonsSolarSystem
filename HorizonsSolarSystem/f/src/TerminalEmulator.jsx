import React, { useState, useEffect, useRef, useCallback } from 'react';
import './TerminalEmulator.css';
import SolarSystem from './SolarSystem';
import PlanetView from './PlanetView';
import { Cpu, Thermometer, Battery, Wifi } from 'lucide-react';

const HomeModule = () => {
  const [cpuUsage, setCpuUsage] = useState(0);
  const [temperature, setTemperature] = useState(0);
  const [batteryLevel, setBatteryLevel] = useState(100);
  const [wifiStrength, setWifiStrength] = useState(0);

  useEffect(() => {
    // Simulate updating widget data
    const interval = setInterval(() => {
      setCpuUsage(Math.floor(Math.random() * 100));
      setTemperature(Math.floor(Math.random() * 50) + 20);
      setBatteryLevel(Math.max(0, batteryLevel - Math.floor(Math.random() * 5)));
      setWifiStrength(Math.floor(Math.random() * 5));
    }, 3000);

    return () => clearInterval(interval);
  }, [batteryLevel]);

  return (
    <div className="home-module">
      <h2>System Status</h2>
      <div className="widget-container">
        <div className="widget">
          <Cpu size={24} />
          <span>CPU: {cpuUsage}%</span>
        </div>
        <div className="widget">
          <Thermometer size={24} />
          <span>Temp: {temperature}°C</span>
        </div>
        <div className="widget">
          <Battery size={24} />
          <span>Battery: {batteryLevel}%</span>
        </div>
        <div className="widget">
          <Wifi size={24} />
          <span>WiFi: {
              wifiStrength === 0 ? 'None' :
              wifiStrength === 1 ? 'Weak' :
              wifiStrength === 2 ? 'Fair' :
              wifiStrength === 3 ? 'Good' :
              'Excellent'
            }</span>
        </div>
      </div>
    </div>
  );
};

const TerminalEmulator = ({ isPlaying, setIsPlaying, volume, setVolume, audioRef }) => {
  const [input, setInput] = useState('');
  const [output, setOutput] = useState(['Welcome. Type "help" for available commands.']);
  const [terminalName, setTerminalName] = useState('');
  const [currentModule, setCurrentModule] = useState('home');
  const [solarSystemData, setSolarSystemData] = useState([]);
  const [selectedPlanet, setSelectedPlanet] = useState(null);
  const inputRef = useRef(null);
  const [currentTime, setCurrentTime] = useState(new Date().toLocaleTimeString());  
  
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);

    return () => clearInterval(timer);
  }, []);  
  
  const [animationsPlayed, setAnimationsPlayed] = useState(false);

  useEffect(() => {
    if (!animationsPlayed) {
      // Sequence the animations only once
      setAnimationsPlayed(true);
    }
  }, [animationsPlayed]);

  useEffect(() => {
    inputRef.current.focus();
    const userAgent = window.navigator.userAgent;
    const lastFiveChars = userAgent.slice(-7);
    setTerminalName(lastFiveChars);

    fetch('/api/solar-system-data/')
      .then(response => response.json())
      .then(data => {
        console.log('Fetched solar system data:', data);
        setSolarSystemData(data);
      })
      .catch(error => console.error('Error fetching solar system data:', error));
  }, []);

  const handleInputChange = useCallback((e) => {
    setInput(e.target.value);
  }, []);

  const handleKeyDown = (e) => {
    e.stopPropagation();
  };

  const StaticTypewriterText = useCallback(({ text }) => {
    const [displayText, setDisplayText] = useState('');
    
    useEffect(() => {
      let i = 0;
      const typingInterval = setInterval(() => {
        if (i < text.length) {
          setDisplayText((prev) => text.substring(0, i + 1));
          i++;
        } else {
          clearInterval(typingInterval);
        }
      }, 35);

      return () => clearInterval(typingInterval);
    }, []); // Empty dependency array

    return <span>{displayText}</span>;
  }, []);

  const TypewriterText = useCallback(({ text }) => {
    const [displayText, setDisplayText] = useState('');
    
    useEffect(() => {
      let i = 0;
      const typingInterval = setInterval(() => {
        if (i < text.length) {
          setDisplayText((prev) => text.substring(0, i + 1));
          i++;
        } else {
          clearInterval(typingInterval);
        }
      }, 35);

      return () => clearInterval(typingInterval);
    }, [text]);

    return <span>{displayText}</span>;
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    e.stopPropagation();
    const fullCommand = input.trim().toLowerCase();
    const [command, ...args] = fullCommand.split(' ');
    let response;

    switch (command) {
      case 'help':
        response = 'Available commands: help, clear, echo, date, map, exit, audio play, audio stop, audio level';
        break;
      case 'clear':
        setOutput([]);
        setInput('');
        return;
      case 'echo':
        response = args.join(' ');
        break;
      case 'date':
        response = new Date().toString();
        break;
      case 'map':
        if (args.length === 0) {
          setCurrentModule('star-map');
          response = 'Entering STAR MAP module. Type "exit" to return home.';
        } else {
          const planetName = args.join(' ');
          const planet = solarSystemData.find(p => p.name.toLowerCase() === planetName.toLowerCase());
          if (planet) {
            setSelectedPlanet(planet);
            setCurrentModule('planet-view');
            response = `Entering PLANETVIS module for ${planet.name}. Type "exit" to return home.`;
          } else {
            response = `Planet "${planetName}" not found.`;
          }
        }
        break;
      case 'exit':
        if (currentModule !== 'home') {
          setCurrentModule('home');
          response = 'Returning to home module.';
        } else {
          response = 'You are already in the home module.';
        }
        break;
      case 'audio':
        if (args.length === 0) {
          response = 'Audio command requires an action. Try "audio play", "audio stop", or "audio level".';
        } else {
          switch (args[0]) {
            case 'play':
              setIsPlaying(true);
              response = 'Audio playback started.';
              break;
            case 'stop':
              setIsPlaying(false);
              response = 'Audio playback stopped.';
              break;
            case 'level':
              if (args.length === 1) {
                response = `Current audio level: ${Math.round(volume * 100)}%. Use 'audio level [0-100]' to set level.`;
              } else {
                const newVolume = parseInt(args[1]) / 100;
                if (!isNaN(newVolume) && newVolume >= 0 && newVolume <= 1) {
                  setVolume(newVolume);
                  response = `Audio level set to ${Math.round(newVolume * 100)}%`;
                } else {
                  response = 'Invalid audio level. Use a number between 0 and 100.';
                }
              }
              break;
            default:
              response = `Unknown audio command: ${args[0]}. Try "audio play", "audio stop", or "audio level".`;
          }
        }
        break;
      default:
        response = `Command not found: ${command}`;
    }

    setOutput([...output, `> ${input}`, response]);
    setInput('');
  };

  const renderModule = useCallback(() => {
    switch (currentModule) {
      case 'star-map':
        return <SolarSystem data={solarSystemData} />;
      case 'planet-view':
        return (
          <PlanetView
            planetName={selectedPlanet.name}
            onClose={() => {
              setCurrentModule('home');
              setSelectedPlanet(null);
            }}
          />
        );
      case 'home':
      default:
        return <HomeModule />;
    }
  }, [currentModule, solarSystemData, selectedPlanet]);

  return (
    <div className="terminal-container crt">
      <div className="display">
        <div className={`top ${animationsPlayed ? 'animate-top' : ''}`}>
          <div className="sysname">
            <StaticTypewriterText text={`INITIATING TERMINAL E.${terminalName}`} />
          </div>
          <div className="systime">
            <StaticTypewriterText text="SYSTEM: " />
            {currentTime}
          </div>
        </div>
        <div className={`bottom ${animationsPlayed ? 'animate-bottom' : ''}`}>
          <div className="crosshair-group crosshair-group-tl">
            <div className="crosshair-quadrant crosshair-quadrant-top-left"></div>
            <div className="crosshair-quadrant crosshair-quadrant-top-right"></div>
            <div className="crosshair-quadrant crosshair-quadrant-bottom-left"></div>
            <div className="crosshair-quadrant crosshair-quadrant-bottom-right"></div>
          </div>
          <div className="crosshair-group crosshair-group-tr">
            <div className="crosshair-quadrant crosshair-quadrant-top-left"></div>
            <div className="crosshair-quadrant crosshair-quadrant-top-right"></div>
            <div className="crosshair-quadrant crosshair-quadrant-bottom-left"></div>
            <div className="crosshair-quadrant crosshair-quadrant-bottom-right"></div>
          </div>
          <div className="crosshair-group crosshair-group-bl">
            <div className="crosshair-quadrant crosshair-quadrant-top-left"></div>
            <div className="crosshair-quadrant crosshair-quadrant-top-right"></div>
            <div className="crosshair-quadrant crosshair-quadrant-bottom-left"></div>
            <div className="crosshair-quadrant crosshair-quadrant-bottom-right"></div>
          </div>
          <div className="crosshair-group crosshair-group-br">
            <div className="crosshair-quadrant crosshair-quadrant-top-left"></div>
            <div className="crosshair-quadrant crosshair-quadrant-top-right"></div>
            <div className="crosshair-quadrant crosshair-quadrant-bottom-left"></div>
            <div className="crosshair-quadrant crosshair-quadrant-bottom-right"></div>
          </div>
          <div className="module-container">
            <TypewriterText text="MODULE" />
            <p className="module">
              <TypewriterText text={currentModule === 'star-map' ? 'STAR MAP' : currentModule.toUpperCase()} />
            </p>
          </div>
          <div className="data">
            {renderModule()}
          </div>
          <div className="sub">
            <div className="cord">
              <TypewriterText text="CORD." />
              <p className="cordata">
                <TypewriterText text="18.2161,-111.4961" />
              </p>
            </div>
            <div>
              <TypewriterText text="AUTOBIS" />
            </div>
            <div className="version">
              <TypewriterText text="122.55.117.5" />
            </div>
          </div>
        </div>
      </div>
      <div className={`terminal ${animationsPlayed ? 'animate-terminal' : ''}`}>
        <div className="terminal-output">
          {output.map((line, index) => (
            <div key={index}>
              <TypewriterText text={line} />
            </div>
          ))}
        </div>
        <form className="terminal-in-containter" onSubmit={handleSubmit}>
          <span className="prompt">{'>'}</span>
          <input
            type="text"
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            ref={inputRef}
            className="terminal-input"
          />
        </form>
      </div>
    </div>
  );
};

export default React.memo(TerminalEmulator);