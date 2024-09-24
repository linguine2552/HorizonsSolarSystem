from django.db import models

class CelestialBody(models.Model):
    BODY_TYPE_CHOICES = [
        ('star', 'Star'),
        ('terrestrial_planet', 'Terrestrial Planet'),
        ('gas_giant', 'Gas Giant'),
        ('dwarf_planet', 'Dwarf Planet'),
        ('major_moon', 'Major Moon'),
        ('moon', 'Moon'),
        ('main_belt_asteroid', 'Main Belt Asteroid'),
        ('near_earth_asteroid', 'Near-Earth Asteroid'),
        ('short_period_comet', 'Short-Period Comet'),
        ('long_period_comet', 'Long-Period Comet'),
        ('kuiper_belt_object', 'Kuiper Belt Object'),
        ('scattered_disc_object', 'Scattered Disc Object'),
        ('trojan_asteroid', 'Trojan Asteroid'),
        ('centaur', 'Centaur'),
        ('unknown', 'Unknown Object'),
    ]
    
    name = models.CharField(max_length=100)
    body_type = models.CharField(max_length=50, choices=BODY_TYPE_CHOICES, default='unknown')
    
    # Physical characteristics
    vol_mean_radius = models.FloatField(help_text="Volume mean radius in km", null=True, blank=True)
    vol_mean_radius_uncertainty = models.FloatField(help_text="Uncertainty in volume mean radius in km", null=True, blank=True)
    density = models.FloatField(help_text="Density in g/cm^3", null=True, blank=True)
    density_uncertainty = models.FloatField(help_text="Uncertainty in density", null=True, blank=True)
    mass = models.FloatField(help_text="Mass in 10^23 kg", null=True, blank=True)
    flattening = models.FloatField(help_text="Flattening, f", null=True, blank=True)
    volume = models.FloatField(help_text="Volume in 10^10 km^3", null=True, blank=True)
    equatorial_radius = models.FloatField(help_text="Equatorial radius in km", null=True, blank=True)
    sidereal_rot_period = models.FloatField(help_text="Sidereal rotation period in hours", null=True, blank=True)
    sid_rot_rate = models.FloatField(help_text="Sidereal rotation rate in rad/s", null=True, blank=True)
    mean_solar_day = models.FloatField(help_text="Mean solar day in seconds", null=True, blank=True)
    polar_gravity = models.FloatField(help_text="Polar gravity in m/s^2", null=True, blank=True)
    core_radius = models.FloatField(help_text="Core radius in km", null=True, blank=True)
    equatorial_gravity = models.FloatField(help_text="Equatorial gravity in m/s^2", null=True, blank=True)
    geometric_albedo = models.FloatField(null=True, blank=True)

    # Gravitational characteristics
    gm = models.FloatField(help_text="GM (gravitational constant * mass) in km^3/s^2", null=True, blank=True)
    gm_uncertainty = models.FloatField(help_text="Uncertainty in GM in km^3/s^2", null=True, blank=True)
    mass_ratio_to_sun = models.FloatField(help_text="Mass ratio (Sun/Body)", null=True, blank=True)
    
    # Atmospheric characteristics
    atmosphere_mass = models.FloatField(help_text="Mass of atmosphere in kg", null=True, blank=True)
    mean_temperature = models.FloatField(help_text="Mean temperature in Kelvin", null=True, blank=True)
    surface_pressure = models.FloatField(help_text="Surface pressure in bar", null=True, blank=True)

    # Orbital characteristics
    obliquity_to_orbit = models.FloatField(help_text="Obliquity to orbit in degrees", null=True, blank=True)
    max_angular_diameter = models.FloatField(help_text="Maximum angular diameter in arcseconds", null=True, blank=True)
    mean_sidereal_orbit_period_years = models.FloatField(help_text="Mean sidereal orbit period in years", null=True, blank=True)
    mean_sidereal_orbit_period_days = models.FloatField(help_text="Mean sidereal orbit period in days", null=True, blank=True)
    visual_magnitude = models.FloatField(help_text="Visual magnitude V(1,0)", null=True, blank=True)
    orbital_speed = models.FloatField(help_text="Orbital speed in km/s", null=True, blank=True)
    hill_sphere_radius = models.FloatField(help_text="Hill's sphere radius in planetary radii", null=True, blank=True)
    escape_speed = models.FloatField(help_text="Escape speed in km/s", null=True, blank=True)

    # Solar interaction
    solar_constant_perihelion = models.FloatField(help_text="Solar Constant at perihelion in W/m^2", null=True, blank=True)
    solar_constant_aphelion = models.FloatField(help_text="Solar Constant at aphelion in W/m^2", null=True, blank=True)
    solar_constant_mean = models.FloatField(help_text="Mean Solar Constant in W/m^2", null=True, blank=True)
    max_planetary_ir_perihelion = models.FloatField(help_text="Maximum Planetary IR at perihelion in W/m^2", null=True, blank=True)
    max_planetary_ir_aphelion = models.FloatField(help_text="Maximum Planetary IR at aphelion in W/m^2", null=True, blank=True)
    max_planetary_ir_mean = models.FloatField(help_text="Mean Maximum Planetary IR in W/m^2", null=True, blank=True)
    min_planetary_ir = models.FloatField(help_text="Minimum Planetary IR in W/m^2", null=True, blank=True)

    # Tertiary Information
    target_pole_equ = models.CharField(max_length=100, help_text="Target pole/equator system", null=True, blank=True)
    target_radii_a = models.FloatField(help_text="Target equatorial radius a in km", null=True, blank=True)
    target_radii_b = models.FloatField(help_text="Target equatorial radius b in km", null=True, blank=True)
    target_radii_c = models.FloatField(help_text="Target polar radius c in km", null=True, blank=True)
    center_geodetic_lon = models.FloatField(help_text="Center geodetic longitude in degrees", null=True, blank=True)
    center_geodetic_lat = models.FloatField(help_text="Center geodetic latitude in degrees", null=True, blank=True)
    center_geodetic_alt = models.FloatField(help_text="Center geodetic altitude in km", null=True, blank=True)
    center_cylindric_lon = models.FloatField(help_text="Center cylindrical longitude in degrees", null=True, blank=True)
    center_cylindric_dxy = models.FloatField(help_text="Center cylindrical Dxy in km", null=True, blank=True)
    center_cylindric_dz = models.FloatField(help_text="Center cylindrical Dz in km", null=True, blank=True)
    center_pole_equ = models.CharField(max_length=100, help_text="Center pole/equator system", null=True, blank=True)
    center_radii_a = models.FloatField(help_text="Center equatorial radius a in km", null=True, blank=True)
    center_radii_b = models.FloatField(help_text="Center equatorial radius b in km", null=True, blank=True)
    center_radii_c = models.FloatField(help_text="Center polar radius c in km", null=True, blank=True)
    target_primary = models.CharField(max_length=100, help_text="Primary body for the target", null=True, blank=True)
    vis_interferer = models.CharField(max_length=100, help_text="Visual interferer", null=True, blank=True)
    vis_interferer_radius = models.FloatField(help_text="Visual interferer radius in km", null=True, blank=True)
    rel_light_bend = models.CharField(max_length=100, help_text="Relative light bending source", null=True, blank=True)
    rel_light_bend_gm = models.FloatField(help_text="Relative light bending GM in km^3/s^2", null=True, blank=True)
    atmos_refraction = models.CharField(max_length=100, help_text="Atmospheric refraction model", null=True, blank=True)
    ra_format = models.CharField(max_length=10, help_text="Right Ascension format", null=True, blank=True)
    time_format = models.CharField(max_length=10, help_text="Time format", null=True, blank=True)
    calendar_mode = models.CharField(max_length=100, help_text="Calendar mode", null=True, blank=True)
    eop_file = models.CharField(max_length=100, help_text="Earth Orientation Parameters file", null=True, blank=True)
    eop_coverage_start = models.DateField(help_text="Start date of EOP coverage", null=True, blank=True)
    eop_coverage_end = models.DateField(help_text="End date of EOP coverage", null=True, blank=True)
    eop_predict_end = models.DateField(help_text="End date of EOP predictions", null=True, blank=True)
    au_km = models.FloatField(help_text="1 AU in km", null=True, blank=True)
    c_km_s = models.FloatField(help_text="Speed of light in km/s", null=True, blank=True)
    day_s = models.FloatField(help_text="1 day in seconds", null=True, blank=True)
    elevation_cutoff = models.FloatField(help_text="Elevation cut-off in degrees", null=True, blank=True)
    airmass_cutoff = models.FloatField(help_text="Airmass cut-off", null=True, blank=True)
    solar_elongation_cutoff_min = models.FloatField(help_text="Minimum solar elongation cut-off in degrees", null=True, blank=True)
    solar_elongation_cutoff_max = models.FloatField(help_text="Maximum solar elongation cut-off in degrees", null=True, blank=True)
    local_hour_angle_cutoff = models.FloatField(help_text="Local Hour Angle cut-off", null=True, blank=True)
    ra_dec_angular_rate_cutoff = models.FloatField(help_text="RA/DEC angular rate cut-off", null=True, blank=True)

    # Osculating orbital elements
    epoch = models.FloatField(help_text="Epoch of osculating elements (Julian Day number)", null=True, blank=True)
    semi_major_axis = models.FloatField(help_text="Semi-major axis (AU)", null=True, blank=True)
    eccentricity = models.FloatField(help_text="Eccentricity", null=True, blank=True)
    inclination = models.FloatField(help_text="Inclination (degrees)", null=True, blank=True)
    mean_longitude = models.FloatField(help_text="Mean longitude (degrees)", null=True, blank=True)
    longitude_of_periapsis = models.FloatField(help_text="Longitude of periapsis (degrees)", null=True, blank=True)
    longitude_of_ascending_node = models.FloatField(help_text="Longitude of ascending node (degrees)", null=True, blank=True)

    # Additional derived elements
    perihelion_distance = models.FloatField(help_text="Perihelion distance (AU)", null=True, blank=True)
    argument_of_perihelion = models.FloatField(help_text="Argument of perihelion (degrees)", null=True, blank=True)
    aphelion_distance = models.FloatField(help_text="Aphelion distance (AU)", null=True, blank=True)
    orbital_period = models.FloatField(help_text="Orbital period (years)", null=True, blank=True)
    mean_motion = models.FloatField(help_text="Mean motion (degrees/day)", null=True, blank=True)
    time_of_perihelion_passage = models.FloatField(help_text="Time of perihelion passage (Julian Day number)", null=True, blank=True)

    # New fields for classification
    is_planet = models.BooleanField(default=False)
    is_moon = models.BooleanField(default=False)
    parent_body = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='satellites')

    # New fields for asteroid and comet classification
    absolute_magnitude = models.FloatField(help_text="Absolute magnitude (H)", null=True, blank=True)
    albedo = models.FloatField(help_text="Geometric albedo", null=True, blank=True)
    tisserand_parameter = models.FloatField(help_text="Tisserand's parameter with respect to Jupiter", null=True, blank=True)

    # Metadata
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Celestial Bodies"