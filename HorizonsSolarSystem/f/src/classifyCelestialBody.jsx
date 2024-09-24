const classifyCelestialBody = (body) => {
  // Helper function to check if a value is within a range
  const isInRange = (value, min, max) => value >= min && value <= max;

  // Sun
  if (body.name.toLowerCase() === 'sun') {
    return 'star';
  }

  // Planets
  if (body.target_primary && body.target_primary.toLowerCase() === 'sun') {
    if (body.vol_mean_radius > 2000 && body.mass > 1e23) {
      return body.atmosphere_mass > 1e16 ? 'gas_giant' : 'terrestrial_planet';
    } else if (body.vol_mean_radius > 500) {
      return 'dwarf_planet';
    }
  }

  // Moons
  if (body.target_primary && body.target_primary.toLowerCase() !== 'sun') {
    return body.vol_mean_radius > 1000 ? 'major_moon' : 'moon';
  }

  // Asteroids
  if (!body.target_primary && body.semi_major_axis < 5.5 && body.eccentricity < 0.4 && body.vol_mean_radius < 500) {
    if (body.semi_major_axis > 2.0 && body.semi_major_axis < 3.3) {
      return 'main_belt_asteroid';
    }
    return 'near_earth_asteroid';
  }

  // Comets
  if (!body.target_primary && (body.eccentricity > 0.8 || body.semi_major_axis > 5.5) && body.vol_mean_radius < 100) {
    return body.orbital_period < 200 * 365.25 ? 'short_period_comet' : 'long_period_comet';
  }

  // Kuiper Belt Objects
  if (!body.target_primary && body.semi_major_axis > 30 && body.semi_major_axis < 55 && body.eccentricity < 0.3) {
    return 'kuiper_belt_object';
  }

  // Scattered Disc Objects
  if (!body.target_primary && body.semi_major_axis > 30 && body.eccentricity >= 0.3 && body.inclination > 10) {
    return 'scattered_disc_object';
  }

  // Trojan Asteroids
  if (!body.target_primary && 
      ((isInRange(body.semi_major_axis, 5.05, 5.35) && body.inclination < 40) || // Jupiter Trojans
       (isInRange(body.semi_major_axis, 9.3, 10.1) && body.inclination < 35))) { // Neptune Trojans
    return 'trojan_asteroid';
  }

  // Centaurs
  if (!body.target_primary && isInRange(body.semi_major_axis, 5.5, 30) && body.eccentricity > 0.1) {
    return 'centaur';
  }

  // If we can't classify it, return 'unknown'
  return 'unknown';
};

export default classifyCelestialBody;