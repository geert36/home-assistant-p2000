# P2000 Sensor

A simple P2000 (Dutch emergency services pager network) sensor for Home Assistant.

The sensor state is the id of the latest notification (unique, changes with every new P2000 message). All details are available as attributes.

## Installation

### HACS (custom repository)

1. In HACS, add `https://github.com/geert36/home-assistant-p2000` as a custom repository (category: integration).
2. Install **P2000 Sensor** and restart Home Assistant.

### Manual

Copy the `custom_components/p2000` folder to `<config_dir>/custom_components/p2000/` and restart Home Assistant.

## Configuration

Go to **Settings → Devices & Services → Add Integration** and search for **P2000**. You can configure everything from the UI:

- **Naam / icoon** — name and icon of the sensor
- **Capcodes** — one or more capcodes, comma separated
- **Gemeenten** — one or more municipalities, comma separated
- **Regio's** — one or more veiligheidsregio's (multi-select)
- **Disciplines** — one or more disciplines (multi-select)
- **Prio 1** — only show priority 1 notifications
- **Update-interval** — how often the API is polled, in seconds (default 30)

When applying multiple properties all will be applied as filter!

All options can be changed later via the **Configure** button on the integration.

### YAML (legacy)

Existing YAML configuration is imported automatically into a config entry. Example:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: p2000
    name: Brandweer
    icon: mdi:fire-truck
    gemeenten:
      - Zwolle
    disciplines:
      - 2

  - platform: p2000
    icon: mdi:ambulance
    name: Ambulance
    gemeenten:
      - Zwolle
    disciplines:
      - 3

  - platform: p2000
    name: IJsselland
    regios:
      - 17

  # Only prio1 of region 17
  - platform: p2000
    name: IJsselland Prio1
    prio1: true
    regios:
      - 17
```

###  regios (Veiligheidsregios)
```
1: Amsterdam-Amstelland
2: Groningen
3: Noord- en Oost Gelderland
4: Zaanstreek-Waterland
5: Hollands Midden
6: Brabant Noord
7: Friesland
8: Gelderland-Midden
9: Kennemerland
10: Rotterdam-Rijnmond
11: Brabant Zuid-Oost
12: Drenthe
13: Gelderland-Zuid
14: Zuid-Holland Zuid
15: Limburg-Noord
17: IJsselland
18: Utrecht
19: Gooi en Vechtstreek
20: Zeeland
21: Limburg-Zuid
23: Twente
24: Noord-Holland Noord
25: Haaglanden
26: Midden- en West Brabant
27: Flevoland
```

## disciplines
```
1: Politie
2: Brandweer
3: Ambulance
4: KNRM
5: Lifeliner
7: DARES
```

## Attributes

| Attribute | Description |
| --- | --- |
| `melding` | Short notification text |
| `tekstmelding` | Full notification text |
| `dienst` | Discipline (Politie, Brandweer, Ambulance, ...) |
| `regio` | Veiligheidsregio name |
| `plaats` | City |
| `postcode` | Postal code |
| `straat` | Street |
| `datum` | Date of the notification |
| `tijd` | Time of the notification |
| `prio1` | `true` when this is a priority 1 notification |
| `brandinfo` | Fire information (if applicable) |
| `grip` | GRIP level (if applicable) |
| `capcodes` | List of capcodes with descriptions |
| `capcodes_str` | Capcodes as a single readable string |
| `latitude` / `longitude` | Coordinates of the notification |
| `last_update_success` | `false` when the last API poll failed; the other attributes then hold the last known notification (possibly outdated) |

You should get a sensor like the following with a lot of attributes.

![P2000 sensor attributes](./assets/screenshot01.png)

Extracting data can be done with a template like:

`{{ state_attr('sensor.p2000_zwolle', 'melding') }}`

## Event entity (recommended for automations)

Besides the sensor, every entry also creates an **event entity** (for a sensor named `Brandweer` this is `event.brandweer_melding`). It fires **once for every new P2000 message**:

| Event type | When |
| --- | --- |
| `melding` | A new incident (the first message) |
| `vervolgmelding` | A follow-up message for an incident you already received, for example when more units are alerted. `parent_id` is the id of the first message |

The event carries the same attributes as the sensor (`melding`, `tekstmelding`, `plaats`, `capcodes_str`, ...) plus `id` and `parent_id`.

Why use it instead of triggering on the sensor?
- Two meldingen within one poll are both reported (the sensor only shows one).
- The sensor shows the incident that was most recently active. When a follow-up arrives for an older incident, the sensor switches back to that older melding, which makes an automation on the sensor fire again for a melding you already handled. The event entity reports each message exactly once.
- Meldingen that exist when Home Assistant starts (or when you change the options) are not reported as new. At most 10 events are fired per update, so an outage cannot flood your notifications.

```yaml
automation:
  - alias: P2000 melding
    triggers:
      - trigger: state
        entity_id: event.brandweer_melding
        not_from: [unavailable, unknown]
    conditions:
      - condition: template
        value_template: "{{ trigger.to_state.attributes.event_type == 'melding' }}"
    actions:
      - action: notify.notify
        data:
          title: "{{ trigger.to_state.attributes.dienst }}"
          message: "{{ trigger.to_state.attributes.melding }}"
```

Remove the condition to also be notified of follow-up messages. The sensor itself works exactly as before, so existing automations keep working.

----------------------------------------------------------------------------------
### lovelace Dashboard

You need markdown and logbook for the following settings

More information on your dashboard.<br> tekst in Dutch.<br>
![afbeelding](./assets/dashboard1.png)

#### markdown card
```
type: markdown
content: >
  Datum : {{ state_attr('sensor.p2000', 'datum' ) }}   Tijd: {{
  state_attr('sensor.p2000', 'tijd') }}


  Melding : {{ state_attr('sensor.p2000', 'melding') }}<br>


  {{ state_attr('sensor.p2000', 'tekstmelding') }}<br>

  -

  Plaats: {{ state_attr('sensor.p2000', 'plaats') }}

  Straat : {{ state_attr('sensor.p2000', 'straat') }} 

  Regio : {{ state_attr('sensor.p2000', 'regio') }}

  capcode : {{ state_attr('sensor.p2000', 'capcodes_str') }}

  lat : {{ state_attr('sensor.p2000', 'latitude') }}  long: {{
  state_attr('sensor.p2000', 'longitude') }}

  <br>

  Dienst: {{ state_attr('sensor.p2000', 'dienst') }}

  info :  {{ state_attr('sensor.p2000', 'brandinfo') }}<br>

  Prio : {{ state_attr('sensor.p2000', 'prio1') }}

  Grip : {{ state_attr('sensor.p2000', 'grip') }}


  Id nr : {{ states('sensor.p2000') }}<br>
```
----------------------------------------------------------------------------------
Also <br>
![afbeelding](./assets/dashboard.png)

#### logbook card
```
type: logbook
entities:
  - sensor.p2000
hours_to_show: 24
title: '112'
```
