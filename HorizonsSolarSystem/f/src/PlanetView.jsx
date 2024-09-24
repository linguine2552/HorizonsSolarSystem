import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { SimplexNoise } from 'three/examples/jsm/math/SimplexNoise';
import { gsap } from 'gsap';
import './PlanetView.css';

const PlanetView = ({ planetName, onClose }) => {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const frameIdRef = useRef(null);
  const [isUnmounting, setIsUnmounting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [planetData, setPlanetData] = useState(null);

  const generateHeightmap = (width, height) => {
    const simplex = new SimplexNoise();
    const heightmap = new Float32Array(width * height);
    
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const nx = x / width - 0.5;
        const ny = y / height - 0.5;
        let elevation = 0;
        
        elevation += simplex.noise(nx * 4, ny * 4) * 0.5;
        elevation += simplex.noise(nx * 8, ny * 8) * 0.25;
        elevation += simplex.noise(nx * 16, ny * 16) * 0.125;
        
        heightmap[y * width + x] = elevation;
      }
    }
    
    return heightmap;
  };

  const createPlanet = (scene, camera) => {
    if (!planetData) return;

    const planetGroup = new THREE.Group();
    planetGroup.name = 'planet';

    const resolution = 128;
    const heightmap = generateHeightmap(resolution, resolution);
    
    const geometry = new THREE.SphereGeometry(planetData.radius, resolution / 2, resolution / 2);
    const positions = geometry.attributes.position;
    const uvs = geometry.attributes.uv;

    const heightAttribute = new Float32Array(positions.count);

    for (let i = 0; i < positions.count; i++) {
      const vertex = new THREE.Vector3();
      vertex.fromBufferAttribute(positions, i);
      
      const uv = new THREE.Vector2();
      uv.fromBufferAttribute(uvs, i);
      
      const xIndex = Math.floor(uv.x * (resolution - 1));
      const yIndex = Math.floor(uv.y * (resolution - 1));
      
      const height = heightmap[yIndex * resolution + xIndex];
      vertex.normalize().multiplyScalar(planetData.radius * (1 + height * 0.1));
      
      positions.setXYZ(i, vertex.x, vertex.y, vertex.z);
      heightAttribute[i] = height;
    }

    geometry.setAttribute('height', new THREE.BufferAttribute(heightAttribute, 1));
    geometry.attributes.position.needsUpdate = true;
    geometry.computeVertexNormals();

    const material = new THREE.ShaderMaterial({
      uniforms: {
        lineColor: { value: new THREE.Color(0x00ff00) },
        topographicLines: { value: 20 },
        lineWidth: { value: 0.02 },
      },
      vertexShader: `
        attribute float height;
        varying float vHeight;
        
        void main() {
          vHeight = height;
          vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
          gl_Position = projectionMatrix * mvPosition;
        }
      `,
      fragmentShader: `
        uniform vec3 lineColor;
        uniform float topographicLines;
        uniform float lineWidth;
        
        varying float vHeight;
        
        void main() {
          float lines = fract(vHeight * topographicLines);
          float smoothLine = smoothstep(0.5 - lineWidth, 0.5, lines) * smoothstep(0.5 + lineWidth, 0.5, lines);
          
          gl_FragColor = vec4(lineColor, smoothLine);
        }
      `,
      transparent: true,
    });

    const planet = new THREE.Mesh(geometry, material);
    planetGroup.add(planet);

    scene.add(planetGroup);

    console.log('Transparent planet with topographic lines added to scene:', planetData);
  };

  useEffect(() => {
    console.log('PlanetView mounted with planetName:', planetName);
    
    // TBD
    const fetchPlanetData = async () => {
      const data = {
        name: planetName,
        radius: 1,
        color: 0x00ff00,
        rotationSpeed: 0.001,
      };
      console.log('Fetched planet data:', data);
      setPlanetData(data);
      setIsLoading(false);
    };

    fetchPlanetData();

    if (!mountRef.current) return;

    const width = mountRef.current.clientWidth;
    const height = mountRef.current.clientHeight;

    const scene = new THREE.Scene();
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
    camera.position.z = 3;
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setClearColor(0x000000, 0);
    mountRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;

    const ambientLight = new THREE.AmbientLight(0x404040);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x00ff00, 2);
    pointLight.position.set(5, 3, 5);
    scene.add(pointLight);

    const animate = () => {
      if (isUnmounting) return;
      frameIdRef.current = requestAnimationFrame(animate);
      controls.update();
      if (scene.getObjectByName('planet')) {
        scene.getObjectByName('planet').rotation.y += 0.0009;
      }
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      const newWidth = mountRef.current.clientWidth;
      const newHeight = mountRef.current.clientHeight;
      camera.aspect = newWidth / newHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(newWidth, newHeight);
    };
    window.addEventListener('resize', handleResize);

    return () => {
      console.log('PlanetView unmounting');
      setIsUnmounting(true);
      if (frameIdRef.current) {
        cancelAnimationFrame(frameIdRef.current);
      }
      if (mountRef.current && rendererRef.current) {
        mountRef.current.removeChild(rendererRef.current.domElement);
      }
      if (rendererRef.current) {
        rendererRef.current.dispose();
      }
      scene.traverse((object) => {
        if (object.geometry) object.geometry.dispose();
        if (object.material) object.material.dispose();
      });
      window.removeEventListener('resize', handleResize);
    };
  }, [planetName]);

  useEffect(() => {
    if (planetData && sceneRef.current && cameraRef.current) {
      createPlanet(sceneRef.current, cameraRef.current);
    }
  }, [planetData]);

  const handleClose = () => {
    console.log('Close button clicked');
    if (mountRef.current) {
      gsap.to(mountRef.current, {
        duration: 1,
        opacity: 0,
        scale: 0.8,
        ease: 'power3.in',
        onComplete: onClose,
      });
    } else {
      onClose();
    }
  };

  return (
    <div className="planet-view-container">
      <div ref={mountRef} className="planet-view-canvas"></div>
      {isLoading && <div className="loading-message">Loading planet data...</div>}
      <div className="planet-name">Planet: {planetName}</div>
      <button className="close-button" onClick={handleClose}>
        Close
      </button>
      {planetData && (
        <div className="planet-data">
          <h3>Planet Data:</h3>
          <p>Name: {planetData.name}</p>
          <p>Radius: {planetData.radius.toFixed(2)}</p>
          <p>Color: {planetData.color.toString(16)}</p>
          <p>Rotation Speed: {planetData.rotationSpeed.toFixed(4)}</p>
        </div>
      )}
    </div>
  );
};

export default PlanetView;