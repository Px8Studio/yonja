# ALİM - Fermerlər üçün mobil tətbiq

## Layihə haqqında

**ALİM** (Fermer tətbiqi) is a live mobile application ecosystem in Azerbaijan developed by **Digital Umbrella** (Digirella), a prominent Azerbaijani tech company specializing in GovTech and AgTech solutions. The platform serves as a "One-Stop Shop" for digital agriculture, designed to bridge the gap between farmers, the government, and the private sector.

**Core Mission:** To digitize the "last mile" of agriculture—bringing services directly to the farmer's smartphone, providing operational information, and helping them manage their activities more efficiently.

---

## Key Features (Existing Platform Capabilities)

### 1. **Əkin bəyanı və subsidiya müraciəti** (Sowing Declarations & Subsidy Applications)
ALİM integrates with **EKTIS** (Electronic Agricultural Information System) to allow farmers to file sowing declarations and apply for government subsidies directly from their phone in 1-2 minutes, without visiting any office.

### 2. **Peyk monitorinqi** (Satellite Monitoring)
Farmers can view satellite imagery of their land plots across different dates, including:
- Vegetation health index (NDVI)
- Moisture index
- Water index

These indicators are displayed on a color scale from weak to high intensity.

### 3. **Aqrar Sığorta Kalkulyatoru** (Agricultural Insurance Calculator)
Enables farmers to pre-calculate insurance costs and plan other expenses accordingly.

### 4. **Aqrokimyəvi analiz** (Agrochemical Analysis)
Farmers can obtain sample codes for agrochemical analysis through the app, even without internet connectivity.

### 5. **Hava proqnozu** (Weather Forecast)
Provides real-time weather data critical for farming, including:
- Precipitation probability
- Relative humidity
- Wind speed
- Temperature

### 6. **Aqrotexnoloji təqvim planı** (Agrotechnological Calendar)
Professional agronomists have prepared monthly action plans for different crop types, guiding farmers on seasonal agricultural practices.

### 7. **Məntəqələr** (Service Points)
Connects farmers to agricultural service and sales points (*satış məntəqələri*), enabling direct contact and faster access to market information.

### 8. **Kənd Təsərrüfatı Nazirliyinə ərizə və müraciət** (Ministry Applications)
Allows farmers to submit applications and proposals directly to the Ministry of Agriculture.

---

## Current State: Transactional Platform

The existing ALİM platform is **transactional**—it records data, processes subsidy requests, and provides information. For example, it can tell a farmer "You declared 5 hectares of wheat" or show satellite imagery, but it **cannot yet provide advisory services** such as "Based on last week's rain, you should delay watering your wheat by 2 days."

---

## The Strategic Challenge: Moving to Advisory

### The Gap
ALİM currently handles official government data (subsidy applications are legal documents) and financial information. The next evolution requires adding an **AI-powered advisory layer** that can provide real-time, personalized recommendations without corrupting the existing legal data infrastructure.

### Data Safety Constraint
Because ALİM processes sensitive government and financial data, **external vendors cannot access production APIs for testing**. Any AI prototype must use **synthetic/dummy data** that mirrors the real data structure without compromising security.

---

## Implications for AI Integration

Any AI enhancement should function as a **plugin module** that:

1. **Sits alongside existing EKTIS integration** without disrupting transactional operations
2. **Maintains separation** between the "Advisory Layer" (recommendations) and "Legal Data Layer" (official records)
3. **Matches the existing UX design language**: Clean interface, green/white color palette, large buttons optimized for outdoor visibility
4. **Operates on synthetic data** during development and testing phases

Digital Umbrella's vision is to equip farmers with innovative tools that enable more productive operations, improve crop quality, and enhance overall farm management through digital support.
