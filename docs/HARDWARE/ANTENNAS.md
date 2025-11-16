# Antenna Systems

## Overview

Antenna selection, installation, and maintenance are critical for reliable vTOC telemetry reception. This guide covers antenna theory, practical construction methods, deployment best practices, and system-specific recommendations for the various RF systems used in vTOC operations.

## Antenna Fundamentals

### Basic Antenna Theory

**Antenna Gain:**
- Measured in dBi (decibels relative to isotropic radiator)
- Higher gain = more focused beam = longer range in specific direction
- 0 dBi = omnidirectional (equal radiation in all directions)
- 3 dBi = doubling of power in preferred direction
- 10 dBi = 10× power in beam direction (narrow beamwidth)

**Polarization:**
- **Vertical:** Best for ground-based mobile communications
- **Horizontal:** Less common, used for specific applications
- **Circular:** Reduces multipath, used for satellite/drone
- **Cross-polarization loss:** 20-30 dB if mismatched

**Impedance Matching:**
- Most systems: 50Ω standard
- Poor match = high VSWR (Voltage Standing Wave Ratio)
- VSWR > 2:1 = significant power reflected back
- Goal: VSWR < 1.5:1 for reliable operation

**Radiation Pattern:**
- **Omnidirectional:** 360° horizontal coverage
- **Directional:** Focused beam (Yagi, patch, dish)
- **Front-to-back ratio:** Rejection of signals from rear
- **Vertical beamwidth:** Coverage in elevation plane

### Frequency vs. Antenna Size

Antenna length is proportional to wavelength (λ):

```
λ (meters) = 300 / frequency (MHz)
```

**Example Calculations:**

| Frequency | Wavelength | 1/4 Wave | 1/2 Wave |
|-----------|-----------|----------|----------|
| **144 MHz (2m)** | 2.08 m | 52 cm | 1.04 m |
| **433 MHz** | 69.3 cm | 17.3 cm | 34.6 cm |
| **915 MHz** | 32.8 cm | 8.2 cm | 16.4 cm |
| **1090 MHz (ADS-B)** | 27.5 cm | 6.9 cm | 13.8 cm |
| **1575 MHz (GPS)** | 19 cm | 4.8 cm | 9.5 cm |
| **2.4 GHz (WiFi)** | 12.5 cm | 3.1 cm | 6.25 cm |

**Design Rule:** 1/4 wave ground plane is minimum practical size for VHF/UHF

## Antenna Types

### Omnidirectional Antennas

#### 1/4 Wave Ground Plane

**Characteristics:**
- Gain: 0-2 dBi
- Pattern: Omnidirectional horizontal, null at zenith
- Impedance: 35-50Ω (depends on radial angle)
- Use case: Mobile, base station with local coverage

**Construction:**
```
Vertical element: λ/4 (e.g., 8.2 cm for 915 MHz)
Radials: 4× λ/4 elements at 45° angle below vertical
Material: 12-14 AWG copper wire or brass rod
```

**Diagram:**
```
        |  ← Vertical element (λ/4)
        |
    ----+----  ← Radials (4× λ/4 at 45° angle)
```

#### 1/2 Wave Vertical (J-Pole)

**Characteristics:**
- Gain: 2-3 dBi
- Pattern: Omnidirectional, lower angle radiation
- Impedance: 50Ω
- Use case: Fixed station, better DX than 1/4 wave

**Construction:**
- Can be built from copper pipe, ladder line, or wire
- Portable versions: Roll-up ladder line J-pole
- Mounting: Vertical, clear of metal obstructions

#### Collinear Array

**Characteristics:**
- Gain: 5-9 dBi (depends on # of elements)
- Pattern: Omnidirectional, low-angle radiation
- Impedance: 50Ω
- Use case: Base station, maximum range

**Examples:**
- Commercial: Diamond X50A, X200A
- DIY: Coaxial collinear (easy to build)

### Directional Antennas

#### Yagi-Uda

**Characteristics:**
- Gain: 6-18 dBi (depends on # of elements)
- Beamwidth: 30-60° (3 dB points)
- Front-to-back: 15-25 dB
- Use case: Point-to-point links, direction finding

**Elements:**
- 1× driven element (dipole)
- 1× reflector (behind driven)
- 1-20× directors (in front of driven)

**Typical Designs:**
- 3-element: 6 dBi gain, 70° beamwidth
- 5-element: 9 dBi gain, 50° beamwidth
- 11-element: 14 dBi gain, 30° beamwidth

#### Log-Periodic

**Characteristics:**
- Gain: 6-10 dBi
- Bandwidth: Multi-octave (e.g., 400-1000 MHz)
- Use case: Wideband monitoring, spectrum analysis

#### Patch Antenna

**Characteristics:**
- Gain: 3-9 dBi
- Pattern: Hemispherical (one side)
- Polarization: Linear or circular
- Use case: GPS, WiFi, panel mount

#### Parabolic Dish

**Characteristics:**
- Gain: 18-30+ dBi
- Beamwidth: 2-10° (very narrow)
- Use case: Long-range point-to-point (microwave)

## Field Construction

### Tools and Materials

**Essential Tools:**
- Wire cutters/strippers
- Soldering iron (60W+) and solder
- Multimeter with continuity tester
- Tape measure / ruler
- Hacksaw or PVC cutter (for support structures)
- Drill and bits

**Materials:**
- Wire: 12-14 AWG copper (solid or stranded)
- Coax: RG-58, RG-8X, or LMR-400
- Connectors: SO-239, N-type, SMA (match to radio)
- PVC pipe: 1/2" to 1" for support structure
- Zip ties: UV-rated for outdoor use
- Heat shrink tubing
- Electrical tape (quality 3M or equiv)
- Silicone sealant (for weatherproofing)

### DIY 1/4 Wave Ground Plane (915 MHz)

**Materials:**
- 4× 8.2 cm copper wire segments (radials)
- 1× 8.2 cm copper wire (vertical element)
- 1× SO-239 chassis connector
- Small piece of copper sheet or PCB

**Instructions:**

1. **Calculate lengths:**
   ```
   915 MHz: λ = 300/915 = 32.8 cm
   1/4 λ = 8.2 cm
   ```

2. **Prepare radials:**
   - Cut 4× 8.2 cm wires
   - Solder to SO-239 mounting holes
   - Bend downward at 45° angle

3. **Vertical element:**
   - Cut 1× 8.2 cm wire
   - Solder to SO-239 center pin
   - Keep vertical (perpendicular to radials)

4. **Test:**
   - Use antenna analyzer or SWR meter
   - Check VSWR < 2:1 at 915 MHz
   - Trim vertical element ±2mm to tune

5. **Weatherproof:**
   - Apply silicone around connections
   - Heat shrink over connections
   - Mount vertically for omnidirectional pattern

### DIY Coaxial Collinear (VHF/UHF)

Great for 2m (144 MHz) or 70cm (433 MHz) bands:

**Materials:**
- RG-58 or RG-8X coax (3-4 meters)
- SO-239 connector
- PVC pipe (1") for support

**Instructions:**

1. **Strip sections:**
   - Mark coax at λ/2 intervals
   - Remove outer jacket (leave shield + center)
   - Every other section: remove shield (leave center only)

2. **Phasing:**
   - Alternate: Shielded / Center-only / Shielded / Center-only
   - Creates in-phase vertical elements
   - Typical: 4-8 elements for 6-9 dBi gain

3. **Support:**
   - Insert coax into PVC pipe
   - Cap top end
   - Mount vertically

4. **Feed:**
   - Bottom coax end: Connect to SO-239
   - Test VSWR
   - Trim length to resonate at target frequency

### Moxon Rectangle (Portable Directional)

Compact directional antenna, easy to build:

**Characteristics:**
- Gain: 6 dBi
- F/B ratio: 20 dB
- Size: ~0.5λ × 0.7λ (much smaller than Yagi)

**Materials:**
- 12 AWG copper wire (2-3 meters for 433 MHz)
- PVC or fiberglass support frame
- SO-239 connector

**Design:**
- Use online Moxon calculator for dimensions
- Enter frequency, get precise measurements
- Build rectangle with specific gap spacing
- Feed point at gap in driven element

**Use Case:** Portable direction finding, temporary P2P links

## Antenna Deployment Methods

### Height Considerations

**"Height is might" in antenna deployment:**

- Every meter of additional height significantly improves range
- Ground clutter (buildings, trees, terrain) limits coverage
- VHF/UHF is primarily line-of-sight

**Height Recommendations:**

| Application | Minimum Height | Optimal Height |
|-------------|----------------|----------------|
| **Base Station** | 6m | 10-15m |
| **Vehicle Mobile** | 1.5m (roof) | 2-3m (mast) |
| **Portable/Handheld** | 1.5m (handheld) | 3m (extended) |
| **Fixed Relay** | 10m | 20-30m |

**Line-of-Sight Calculation:**

```
Distance (km) = 3.57 × (√h1 + √h2)
where h1, h2 = antenna heights in meters
```

**Example:**
- Station A: 10m antenna height
- Station B: 10m antenna height
- LOS distance = 3.57 × (√10 + √10) = 22.6 km

### Mounting Methods

#### Mast Mount

**Materials:**
- Galvanized steel or aluminum mast (1-2" diameter)
- Guy wires (for heights > 3m)
- Concrete base or roof mount
- U-bolts for antenna attachment

**Installation:**
1. Anchor mast securely (guy wires at 3 points, 120° apart)
2. Route coax inside or alongside mast
3. Use drip loop at bottom (prevent water entry)
4. Attach antenna at top with U-bolts
5. Weatherproof all connections

#### Roof/Soffit Mount

**Materials:**
- Roof vent pipe mount or chimney bracket
- Non-penetrating roof mount (alternative)
- Stainless steel hardware

**Installation:**
1. Avoid penetrating roof if possible (leaks)
2. Use existing vent pipe mounts
3. Or use non-penetrating base with weight/straps
4. Route coax to attic/exterior wall
5. Seal any roof penetrations with quality sealant

#### Vehicle Mount

**Types:**
- **Magnetic mount:** Quick deploy, good for temporary
- **NMO mount:** Permanent, requires hole in vehicle
- **Lip/gutter mount:** Clamps to trunk/hood
- **Mirror/bumper mount:** Alternative mounting points

**Best Practices:**
- Center roof mount = best pattern
- Avoid mounting near metal obstructions
- Use quality coax (minimize loss)
- Ground mount to vehicle chassis (NMO)

#### Portable/Field Deploy

**Methods:**
- Telescoping mast (fiberglass poles)
- Tripod with mast
- Tree/structure mount (temporary)
- Kite/balloon lift (advanced)

**Considerations:**
- Stability in wind
- Quick setup/teardown
- Lightweight materials
- Weatherproof connections (field conditions)

## Gain Considerations

### Gain vs. Coverage

**Higher Gain Tradeoffs:**

✅ **Advantages:**
- Longer range in beam direction
- Better SNR (signal-to-noise ratio)
- Overcome path loss

❌ **Disadvantages:**
- Narrower beamwidth
- Must aim precisely
- Vertical pattern narrows (near-field coverage reduced)

**Example: 915 MHz Base Station**

| Antenna | Gain | Hor. Pattern | Ver. Beamwidth | Use Case |
|---------|------|--------------|----------------|----------|
| **1/4 Wave GP** | 0 dBi | Omnidirectional | 90° | Local coverage |
| **1/2 Wave** | 2 dBi | Omnidirectional | 60° | Balanced |
| **5 dBi Collinear** | 5 dBi | Omnidirectional | 30° | Long range, flat terrain |
| **9 dBi Collinear** | 9 dBi | Omnidirectional | 15° | Very long range, but poor near-field |

**Deployment Rule:**
- **Urban/hilly:** Lower gain (wider vertical pattern)
- **Flat/open:** Higher gain (concentrate power at horizon)
- **Mobile:** Low gain (coverage while moving)

### Link Budget

Calculate if link is viable:

```
Received Power (dBm) = TX Power (dBm) + TX Ant Gain (dBi)
                        - Path Loss (dB) + RX Ant Gain (dBi)
                        - Cable Loss (dB)
```

**Example: 915 MHz, 5 km Link**

```
TX Power: +20 dBm (100 mW)
TX Antenna: +5 dBi (collinear)
Path Loss (5 km, 915 MHz): -113 dB
RX Antenna: +5 dBi (collinear)
Cable Loss (both ends): -3 dB

Received Power = 20 + 5 - 113 + 5 - 3 = -86 dBm

RX Sensitivity: -110 dBm (typical LoRa)
Link Margin: -86 - (-110) = 24 dB ✓ (Good!)
```

**Target Link Margin:** 10-20 dB minimum for reliable operation

## Cabling and Connectors

### Coaxial Cable Types

| Cable Type | Loss @ 915 MHz | Use Case | Cost |
|------------|----------------|----------|------|
| **RG-174** | 1.5 dB/m | <1m patch cables | $ |
| **RG-58** | 0.65 dB/m | <5m runs | $ |
| **RG-8X** | 0.40 dB/m | <10m runs | $$ |
| **LMR-200** | 0.27 dB/m | <15m runs | $$ |
| **LMR-400** | 0.14 dB/m | >15m runs | $$$ |
| **LMR-600** | 0.09 dB/m | Long runs (>50m) | $$$$ |

**Selection Guide:**
- **Short runs (<3m):** RG-58 is sufficient, low cost
- **Medium runs (3-10m):** RG-8X or LMR-200
- **Long runs (>10m):** LMR-400 mandatory (loss matters!)
- **Avoid:** RG-58 for runs > 5m at UHF frequencies

**Loss Example:**
```
10m run at 915 MHz:
- RG-58: 10m × 0.65 dB/m = 6.5 dB loss (Ouch!)
- LMR-400: 10m × 0.14 dB/m = 1.4 dB loss (Much better)

6.5 dB loss = 77% power wasted as heat!
1.4 dB loss = 28% power wasted
```

### Connectors

**Common Types:**

- **BNC:** Quick disconnect, <1 GHz, labs/test equipment
- **SMA:** Threaded, compact, up to 18 GHz, common on SDR
- **N-Type:** Weatherproof, threaded, up to 11 GHz, outdoor
- **SO-239 (UHF):** Old standard, <300 MHz ideally, still common
- **RP-SMA:** Reverse polarity (WiFi devices, regulatory)

**Best Practices:**
- Match connector to cable type (proper crimp/solder)
- Use quality connectors (cheap = high loss)
- Weatherproof outdoor connections (heatshrink + tape + silicone)
- Minimize connector count (each adds 0.1-0.5 dB loss)

### Cable Installation

**Outdoor Runs:**

1. **UV Protection:**
   - Use UV-rated coax (black jacket)
   - Or enclose in conduit

2. **Water Protection:**
   - Drip loops before connectors
   - Seal all connections (heat shrink + self-amalgamating tape + silicone)
   - Never point connector upward (water collects)

3. **Physical Protection:**
   - Secure with UV-rated zip ties every 30cm
   - Avoid sharp bends (radius > 5× cable diameter)
   - Protect from foot/vehicle traffic

4. **Routing:**
   - Keep away from AC power lines (interference)
   - Avoid parallel runs with power (separation > 30cm)
   - Ground at entry point (lightning protection)

## Grounding and Lightning Protection

### Importance

Lightning strikes or nearby strikes can:
- Destroy radios (static discharge)
- Damage computers/networks (surge via cables)
- Create fire hazard (arcing)

**Protection Strategy:** Multi-layer defense

### Antenna Grounding

**DC Ground:**
- Connect antenna mast to ground rod
- Use #6 AWG or larger copper wire
- Short, direct path to ground (<3m ideal)
- Ground rod: 8-10 feet copper-clad steel

**RF Ground:**
- Coax shield connects to mast/ground at antenna
- Creates low-impedance path for static discharge
- Does NOT affect RF performance (AC-coupled at radio end)

### Coaxial Lightning Protection

**Bulkhead Arrestor:**
- Installs in-line with coax at entry point
- Gas discharge tube (GDT) shorts to ground during surge
- Low insertion loss (< 0.5 dB)
- Must have short ground wire to ground rod

**Example Products:**
- PolyPhaser: IS-50UX-C2 (0-6 GHz, N-type)
- Alpha Delta: TT3G50U (0-500 MHz, SO-239)

**Installation:**

```
Antenna → Coax → [Arrestor] → Coax → Radio
                      ↓
                   Ground Rod
```

**Critical:** Ground wire from arrestor must be <1m to ground rod
- Long ground wire = ineffective (inductance)
- Use copper strap or #6 AWG wire
- Straight path, no sharp bends

### Facility Grounding

**Single Point Ground:**
- All equipment grounds converge at one point
- Prevents ground loops (interference)
- Use copper busbar or ground panel
- Connect to ground rod system

**Ground Rod System:**
- Minimum: 1× 8-10 ft ground rod
- Better: 2-3 ground rods bonded together (separation: 6-10 ft)
- Best: Ground ring around building (buried #2 AWG copper)

### Lightning Safety Best Practices

1. **Disconnect:**
   - Unplug equipment during thunderstorms (if manned)
   - Coax arrestors protect, but not 100%
   - Direct strike = expensive lesson

2. **Insurance:**
   - Document all equipment
   - Consider rider for amateur radio/electronics gear
   - Photograph installations (proof of proper grounding)

3. **Risk Assessment:**
   - Low-risk: Mobile installations (car), temporary setups
   - High-risk: Permanent outdoor antennas, towers
   - Very high-risk: Mountain-top installations

4. **Don't Skimp:**
   - Quality arrestors: $30-100
   - Damaged radio: $500-5000
   - Fire damage: Priceless

## System-Specific Recommendations

### ADS-B (1090 MHz)

**Antenna:**
- Type: 1/4 wave vertical collinear
- Gain: 2-5 dBi
- Pattern: Omnidirectional
- Polarization: Vertical

**Products:**
- FlightAware ProStick Plus (filtered LNA + antenna)
- Jetvision A3 (high gain collinear)

**DIY:**
- 1/4 wave ground plane: 6.9 cm vertical, 4× 6.9 cm radials
- Coaxial collinear: 4-8 elements for 5-8 dBi

**Mounting:**
- Roof-mounted, clear LOS to sky
- Height: 3-10m (higher = better aircraft count)
- Keep clear of obstructions (buildings, trees)

**Cable:**
- LMR-400 for runs > 10m
- Include 1090 MHz SAW filter (prevents overload)

### GPS (1575 MHz, L1 Band)

**Antenna:**
- Type: Patch antenna with ground plane
- Gain: 26-28 dBi typical (active antenna)
- Polarization: Right-hand circular (RHCP)
- Pattern: Hemispherical (upper hemisphere)

**Products:**
- U-blox ANN-MB (embedded, passive)
- Taoglas GPS.25 (active, magnetic mount)
- External active GPS antenna (SMA)

**Mounting:**
- Flat surface, facing sky
- No obstructions above 15° elevation
- Keep away from metal (or use ground plane)
- Avoid carbon fiber (blocks GPS signals)

**Cable:**
- Use low-loss coax (LMR-200 or better)
- Minimize length (active antennas have gain to compensate)
- Power via coax (if active antenna)

**EMI Considerations:**
- GPS is extremely weak signal (-130 dBm at antenna)
- Keep away from:
  - USB 3.0 devices (harmonics interfere)
  - Switch-mode power supplies
  - Transmitters (even 915 MHz LoRa)
- Separation: >30 cm minimum from other antennas

### LoRa (433/868/915 MHz)

**Base Station Antenna:**
- Type: 1/2 wave vertical or collinear
- Gain: 3-9 dBi (depending on terrain)
- Pattern: Omnidirectional
- Mounting: 6-10m height

**Mobile/Node Antenna:**
- Type: 1/4 wave whip or stubby
- Gain: 0-3 dBi
- Pattern: Omnidirectional
- Mounting: Vertical, clear of metal

**Products:**
- 915 MHz: 3dBi stubby (portable), 5 dBi fiberglass (fixed)
- 868 MHz: Same, adjusted for frequency
- 433 MHz: Larger (λ longer), same principles

**Directional (P2P):**
- Yagi: 10-15 dBi (point fixed links)
- Use for difficult paths (mountains, urban canyon)

**Cable:**
- RG-58 okay for <5m
- LMR-200/LMR-400 for longer runs
- Keep losses low (every dB counts on LoRa)

### WiFi HaLow (915 MHz Sub-1 GHz)

**Access Point Antenna:**
- Type: Omnidirectional or sector
- Gain: 5-9 dBi
- Mounting: High point, clear LOS

**Client/Node Antenna:**
- Type: Omnidirectional or directional
- Gain: 3-10 dBi (directional for P2P)
- Mounting: Aimed at AP (directional)

**Point-to-Point:**
- Use Yagi or panel antennas (both ends)
- Gain: 10-15 dBi each end
- Enables 2-5 km links (LOS)

### VHF (144 MHz, 2m Band)

**APRS/Voice:**
- Base: 1/2 wave vertical or 5/8 wave (3 dBi)
- Mobile: 1/4 wave on vehicle roof (mag mount)
- Handheld: Rubber duck (0 dBi) or extended whip (2 dBi)

**Products:**
- Diamond X50A (dual-band 2m/70cm collinear)
- Larsen NMO-2/70 (mobile, roof mount)

**Mounting:**
- Height critical for VHF (very line-of-sight)
- Vehicle: Center roof best, hood/trunk okay
- Fixed: 10m+ for regional coverage

## Antenna Testing and Tuning

### Tools

**SWR Meter:**
- Measures impedance match
- Forward power vs. reflected power
- Goal: SWR < 1.5:1

**Antenna Analyzer:**
- More capable than SWR meter
- Shows impedance (R + jX)
- Sweep frequency range
- Examples: NanoVNA, rigExpert, MFJ-259

**Spectrum Analyzer:**
- Measure antenna pattern (requires test source)
- Identify interference sources
- Verify filter performance

### Tuning Procedure

1. **Initial Test:**
   - Connect analyzer to antenna
   - Measure SWR across frequency range
   - Note resonant frequency (lowest SWR)

2. **Adjust Length:**
   - Too low frequency: Shorten antenna (remove length)
   - Too high frequency: Lengthen antenna (add length)
   - Rule of thumb: 1% length change = 1% frequency change

3. **Iterative Tuning:**
   - Make small adjustments (2-3mm)
   - Re-measure after each change
   - Converge on target frequency

4. **Bandwidth Check:**
   - Measure SWR at band edges
   - Verify acceptable across full bandwidth
   - Wider bandwidth = more forgiving (less tune-sensitive)

### Field Testing

**Signal Strength:**
- Use receiver with S-meter or dBm display
- Measure signal from known source at distance
- Compare different antennas or mounting positions

**Coverage Mapping:**
- Mobile test: Drive around with receiver
- Log GPS position + signal strength
- Plot on map to visualize coverage
- Tools: RF Explorer, SDR + GPS logger

**Practical Test:**
- Real-world usage (not just bench test)
- Verify range meets requirements
- Test in various conditions (weather, time of day)

## Troubleshooting

### Poor Performance

**Symptoms:**
- Short range
- Weak signal
- High noise

**Checks:**

1. **SWR:** Measure at antenna connector (not radio)
   - High SWR = poor match or damaged antenna/cable

2. **Cable loss:** Excessive loss = short range
   - Use quality cable (LMR-400 for long runs)
   - Check connectors (loose, corroded?)

3. **Antenna height:** Low antenna = ground clutter limits range
   - Raise antenna even 1-2m (every meter helps)

4. **Obstructions:** Buildings, trees, terrain block UHF/VHF
   - Relocate to clear LOS

5. **Interference:** Noise floor high
   - Identify sources (spectrum analyzer)
   - Filter, relocate, or shield

### Intermittent Issues

**Symptoms:**
- Works sometimes, fails others
- Weather dependent

**Checks:**

1. **Water ingress:** Moisture in connectors/cable
   - Reseal all outdoor connections
   - Inspect cable jacket for damage

2. **Loose connection:** Vibration, thermal expansion
   - Tighten all connectors
   - Use lock washers, Loctite on screws

3. **Oxidation:** Connector corrosion over time
   - Clean with contact cleaner
   - Replace if severe
   - Apply dielectric grease

## Maintenance Schedule

### Monthly
- Visual inspection of outdoor antennas
- Check for physical damage (wind, ice, animals)
- Verify mast/mounting security

### Quarterly
- Detailed connector inspection
- Clean antennas (dust, bird droppings)
- Test SWR (detect degradation early)
- Re-torque all fasteners

### Annually
- Replace weatherproofing (tape, silicone)
- Deep clean all antennas
- Inspect cable runs (UV damage, chafing)
- Consider cable replacement if >5 years old (UV degrades jacket)

### After Severe Weather
- Full visual inspection
- SWR test (lightning strike can damage)
- Check ground connections
- Verify mast alignment (straight, not bent)

## Related Documentation

- [RTL-SDR](RTL-SDR.md) - ADS-B antenna requirements
- [LoRa MANET Node](LORA-MANET.md) - LoRa mesh antenna selection
- [WiFi HaLow Bridge](WIFI-HALOW-BRIDGE.md) - HaLow antenna optimization
- [BYONICS PiCon](BYONICS-PICON.md) - APRS antenna setup
- [Geospatial Mesh Planning](../MESH_PLANNING/OVERVIEW.md) - Coverage area planning

## External Resources

- [ARRL Antenna Book](http://www.arrl.org/shop/ARRL-Antenna-Book/) - Comprehensive reference
- [Online Antenna Calculators](https://www.qsl.net/in3ota/){:target="_blank"}
- [NanoVNA User Guide](https://nanovna.com/)
- [Practical Antenna Handbook (Carr)](https://www.amazon.com/Practical-Antenna-Handbook-Joseph-Carr/dp/0071639586)
- [VK5DJ Antenna Calculator](http://www.vk5dj.com/calc.html)
