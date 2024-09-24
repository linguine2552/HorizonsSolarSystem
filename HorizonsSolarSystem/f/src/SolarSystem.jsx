import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { CSS2DRenderer, CSS2DObject } from 'three/examples/jsm/renderers/CSS2DRenderer';
import './SolarSystem.css';

const SolarSystem = ({ data }) => {
  const mountRef = useRef(null);
  const [is2DView, setIs2DView] = useState(true);
  const controlsRef = useRef(null);
  const cameraRef = useRef(null);
  const keysPressed = useRef({});
  const [visibilityFilter, setVisibilityFilter] = useState('all');
  const [bodies, setBodies] = useState([]);
  const [selectedBody, setSelectedBody] = useState(null);
  const [glossarySearchTerm, setGlossarySearchTerm] = useState('');
  const [isGlossaryVisible, setIsGlossaryVisible] = useState(true);  
  const [areLabelsVisible, setAreLabelsVisible] = useState(true);  
  const [cameraState, setCameraState] = useState(null);  

  // Define dictionaries for different categories of celestial bodies
  const planets = {
    'Mercury': true,
    'Venus': true,
    'Earth': true,
    'Mars': true,
    'Jupiter': true,
    'Saturn': true,
    'Uranus': true,
    'Neptune': true,
    'Pluto': true
  };

  const gasGiants = {
    'Jupiter': true,
    'Saturn': true,
    'Uranus': true,
    'Neptune': true
  };

  const dwarfPlanets = {
    'Pluto': true,
    'Ceres': true,
    'Eris': true,
    'Haumea': true,
    'Makemake': true
  };
  
  const saveCameraState = () => {
    if (cameraRef.current && controlsRef.current) {
      setCameraState({
        position: cameraRef.current.position.clone(),
        rotation: cameraRef.current.rotation.clone(),
        zoom: cameraRef.current.zoom,
        target: controlsRef.current.target.clone()
      });
    }
  };

  const restoreCameraState = (state) => {
    if (cameraRef.current && controlsRef.current && state) {
      cameraRef.current.position.copy(state.position);
      cameraRef.current.rotation.copy(state.rotation);
      cameraRef.current.zoom = state.zoom;
      cameraRef.current.updateProjectionMatrix();
      controlsRef.current.target.copy(state.target);
      controlsRef.current.update();
    }
  };  

  useEffect(() => {
    const container = mountRef.current;
    const scene = new THREE.Scene();
    
    const camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000000);
    cameraRef.current = camera;
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });

    renderer.setSize(container.clientWidth, container.clientHeight);
    container.appendChild(renderer.domElement);

    const labelRenderer = new CSS2DRenderer();
    labelRenderer.setSize(container.clientWidth, container.clientHeight);
    labelRenderer.domElement.style.position = 'absolute';
    labelRenderer.domElement.style.top = '0';
    container.appendChild(labelRenderer.domElement);

    const controls = new OrbitControls(camera, labelRenderer.domElement);
    controlsRef.current = controls;

    // Set initial camera position for side view
    camera.position.set(0, 0, 50);
    camera.lookAt(0, 0, 0);
    controls.update();

    controls.maxDistance = 100;  // In AU units

    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);

    const light = new THREE.PointLight(0xffffff, 1, 1000);
    light.position.set(0, 0, 0);
    scene.add(light);

    const AU = 149597870.7; // Astronomical Unit in km
    const scaleFactor = 1 / AU;  // Scale 1 AU to 1 unit in our 3D space
    const bodySizeFactor = 50000;  // Adjust this value to make bodies more visible

    const focusOnBody = (body) => {
      const position = new THREE.Vector3(body.x, body.y, body.z);
      const distance = body.radius * 5; // Adjust this multiplier as needed
      const newCameraPosition = position.clone().add(new THREE.Vector3(distance, 0, 0));
      
      camera.position.copy(newCameraPosition);
      controls.target.copy(position);
      controls.update();
    };

    if (selectedBody) {
      const body = bodies.find(b => b.body.name === selectedBody);
      if (body) {
        focusOnBody(body.body);
      }
    }

    const createBodies = () => {
      return data.filter(body => body.x !== undefined && body.y !== undefined && body.z !== undefined)
        .map((body) => {
          const scaledRadius = Math.max((body.radius * bodySizeFactor * scaleFactor), 0.01);
          const geometry = new THREE.SphereGeometry(scaledRadius, 32, 32);
          
          let material;
          if (body.body_type === 'star') {
            material = new THREE.MeshBasicMaterial({ color: 0xffff00 });  // Yellow for the Sun
          } else if (body.body_type === 'terrestrial_planet') {
            material = new THREE.MeshBasicMaterial({ color: 0x4169e1 });  // Blue for terrestrial planets
          } else if (body.body_type === 'gas_giant') {
            material = new THREE.MeshBasicMaterial({ color: 0xffa500 });  // Orange for gas giants
          } else {
            material = new THREE.MeshBasicMaterial({ color: 0x808080 });  // Gray for other bodies
          }
          
          const mesh = new THREE.Mesh(geometry, material);

          mesh.position.set(body.x, body.y, body.z);
          
          mesh.frustumCulled = false;
          scene.add(mesh);

          const labelDiv = document.createElement('div');
          labelDiv.className = 'label';
          labelDiv.textContent = body.name.toUpperCase();
          const label = new CSS2DObject(labelDiv);
          label.position.set(0, scaledRadius + 0.01, 0);
          label.visible = areLabelsVisible;
          mesh.add(label);

          return { mesh, label, body };
        });
    };

    const createdBodies = createBodies();
    setBodies(createdBodies);

    const handleResize = () => {
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
      labelRenderer.setSize(container.clientWidth, container.clientHeight);
    };

    window.addEventListener('resize', handleResize);

    const handleKeyDown = (event) => {
      keysPressed.current[event.key.toLowerCase()] = true;
    };

    const handleKeyUp = (event) => {
      keysPressed.current[event.key.toLowerCase()] = false;
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);

    const moveCamera = () => {
      const baseMoveSpeed = 0.5;
      const zoomFactor = camera.position.length() / 30;
      const moveSpeed = baseMoveSpeed * zoomFactor;

      const movement = new THREE.Vector3(0, 0, 0);

      if (keysPressed.current['w']) movement.y += moveSpeed;
      if (keysPressed.current['s']) movement.y -= moveSpeed;
      if (keysPressed.current['a']) movement.x -= moveSpeed;
      if (keysPressed.current['d']) movement.x += moveSpeed;

      camera.position.add(movement);
      controls.target.add(movement);
      controls.update();
    };

    const animate = () => {
      requestAnimationFrame(animate);
      if (is2DView) {
        moveCamera();
      }
      renderer.render(scene, camera);
      labelRenderer.render(scene, camera);
    };
    animate();

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
      window.removeEventListener('resize', handleResize);
      container.removeChild(renderer.domElement);
      container.removeChild(labelRenderer.domElement);
    };
  }, [data, selectedBody]);

  useEffect(() => {
    if (controlsRef.current && cameraRef.current) {
      const camera = cameraRef.current;
      const controls = controlsRef.current;

      if (is2DView) {
        // Set camera for side view in 2D mode
        camera.position.set(0, 0, 50);
        camera.lookAt(0, 0, 0);
        controls.enableRotate = false;
        controls.enableZoom = true;
        controls.enablePan = true;
        controls.maxPolarAngle = Math.PI / 2;
        controls.minPolarAngle = Math.PI / 2;
      } else {
        // Set camera for 3D view
        camera.position.set(30, 30, 30);
        camera.lookAt(0, 0, 0);
        controls.enableRotate = true;
        controls.enableZoom = true;
        controls.enablePan = true;
        controls.maxPolarAngle = Math.PI;
        controls.minPolarAngle = 0;
      }
      controls.update();
    }
  }, [is2DView]);

  useEffect(() => {
    if (cameraState) {
      restoreCameraState(cameraState);
    }

    if (controlsRef.current && cameraRef.current) {
      const controls = controlsRef.current;

      if (is2DView) {
        controls.enableRotate = false;
        controls.maxPolarAngle = Math.PI / 2;
        controls.minPolarAngle = Math.PI / 2;
      } else {
        controls.enableRotate = true;
        controls.maxPolarAngle = Math.PI;
        controls.minPolarAngle = 0;
      }
      controls.update();
    }

    bodies.forEach(({ label }) => {
      if (label) {
        label.visible = areLabelsVisible;
      }
    });
  }, [is2DView, cameraState, areLabelsVisible, bodies]);

  const toggleView = () => {
    saveCameraState();
    setIs2DView(!is2DView);
  };

  const handleVisibilityFilterChange = (event) => {
    setVisibilityFilter(event.target.value);
  };

  const filteredBodiesForVisibility = bodies.filter(({ body }) => {
    // Always include the sun
    if (body.body_type === 'star') return true;

    switch (visibilityFilter) {
      case 'planets':
        return planets[body.name];
      case 'gas_giants':
        return gasGiants[body.name];
      case 'dwarf_planets':
        return dwarfPlanets[body.name];
      case 'all':
      default:
        return true;
    }
  });


useEffect(() => {
  filteredBodiesForVisibility.forEach(({ mesh, label }) => {
    mesh.visible = true;
    label.visible = areLabelsVisible;  // Respect the label visibility state
  });

  bodies.forEach(({ mesh, label }) => {
    if (!filteredBodiesForVisibility.find(b => b.mesh === mesh)) {
      mesh.visible = false;
      label.visible = false;
    }
  });
}, [visibilityFilter, bodies, filteredBodiesForVisibility, areLabelsVisible]);  // Add areLabelsVisible to dependencies

  const handleBodySelect = (bodyName) => {
    setSelectedBody(bodyName);
  };
  
  const handleGlossarySearchChange = (event) => {
    setGlossarySearchTerm(event.target.value);
  };

  const filteredGlossaryBodies = data.filter((body) => {
    return body.name.toLowerCase().includes(glossarySearchTerm.toLowerCase());
  });

  useEffect(() => {
    bodies.forEach(({ label }) => {
      label.visible = areLabelsVisible;
    });
  }, [areLabelsVisible, bodies]);

  const toggleGlossary = () => {
    setIsGlossaryVisible(!isGlossaryVisible);
  };

  const toggleLabels = () => {
    saveCameraState();
    setAreLabelsVisible(!areLabelsVisible);
  };
  
  

  return (
    <div className="solar-system-container">
      <div ref={mountRef} className="solar-system-container" />
      <button 
        onClick={toggleView} 
        className="view-toggle-button"
      >
        {is2DView ? '3D View' : '2D View'}
      </button>
      <button 
        onClick={toggleLabels} 
        className="labels-toggle-button"
      >
        {areLabelsVisible ? 'Hide Labels' : 'Show Labels'}
      </button>
      <div className="filter-container">
        <select value={visibilityFilter} onChange={handleVisibilityFilterChange} className="filter-select">
          <option value="all">All Bodies</option>
          <option value="planets">Planets</option>
          <option value="gas_giants">Gas Giants</option>
          <option value="dwarf_planets">Dwarf Planets</option>
        </select>
      </div>
      <button 
        onClick={toggleGlossary} 
        className="glossary-toggle-button"
      >
        {isGlossaryVisible ? 'Hide Glossary' : 'Show Glossary'}
      </button>
      <div className={`glossary-container ${isGlossaryVisible ? 'visible' : 'hidden'}`}>
        <h3>Celestial Bodies Glossary</h3>
        <input
          type="text"
          placeholder="Search celestial bodies..."
          value={glossarySearchTerm}
          onChange={handleGlossarySearchChange}
          className="search-input"
        />
        <ul>
          {filteredGlossaryBodies.map((body) => (
            <li 
              key={body.name}
              onClick={() => handleBodySelect(body.name)}
              className={`glossary-item ${selectedBody === body.name ? 'selected' : ''}`}
            >
              {body.name} - {body.body_type}
            </li>
          ))}
        </ul>
      </div>
      <div className="star-map-label">
        {selectedBody && `Focused on: ${selectedBody}`}
      </div>
      {is2DView && (
        <div className="controls-info">
          Use WASD keys to move the camera
        </div>
      )}
    </div>
  );
};

export default SolarSystem;