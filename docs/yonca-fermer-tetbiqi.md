Based on the public information about **Digital Umbrella** and their **Yonca** platform, here is what is known. This context confirms that the challenge you have been given is grounded in a very real, mature product ecosystem, which makes the "Dummy Data" constraint critical (due to the sensitivity of the actual government/farmer data they handle).

### 1. What is "Yonca"?

**Yonca** (often styled as "YONCA | Fermer tətbiqi") is a live mobile application ecosystem in Azerbaijan designed to bridge the gap between farmers, the government, and the private sector. It acts as a "One-Stop Shop" for digital agriculture.

* **Developer:** Digital Umbrella (also known as Digirella), a prominent Azerbaijani tech company specializing in GovTech and AgTech solutions.
* **Core Mission:** To digitize the "last mile" of agriculture—bringing services directly to the farmer's smartphone.

### 2. Key Existing Features (The "Real Data" You Cannot Touch)

The features mentioned in your prompt are not hypothetical; they are existing modules in the live Yonca app. This explains why they are so strict about **Data Safety**. The app currently handles:

* **Government Services:** It integrates with **EKTIS** (Electronic Agricultural Information System) to allow farmers to file **Sowing Declarations (Əkin bəyanı)** and apply for **Subsidies (Subsidiya müraciəti)** directly from the phone.
* **Satellite Monitoring:** Users can view satellite imagery of their land plots (*Peyk monitorinqi*) to check vegetation health.
* **Financial Tools:** It includes calculators for **Agricultural Insurance** (Aqrar Sığorta) and credit estimations.
* **Market & Operations:** It connects farmers to sales points (*satış məntəqələri*) and provides weather and agrotechnological calendars.

### 3. Why This "AI Prototype" Challenge Exists

The current Yonca platform is **Transactional** (it records data and requests subsidies). The challenge asks you to move it to **Advisory** (it tells the farmer *what to do*).

* **The Gap:** Currently, Yonca can tell a farmer "You declared 5 hectares of wheat." It *cannot* yet reliably tell them, "Based on the rain last week, you should delay watering your wheat by 2 days."
* **The Constraint:** Because Yonca handles official government data (subsidy applications are legal documents) and financial data, they cannot expose their API to a 3rd party vendor for testing. This is why they are forcing you to build a **Synthetic Engine**.

### 4. Strategic Advice for Your Response

Since Yonca is already a polished product, your prototype shouldn't try to "rebuild" the app. It should look like a **Plugin Module** that fits silently into their existing architecture.

* **UX Note:** Match their existing design language (Clean, green/white palette, large buttons for outdoor visibility).
* **Integration:** In your "Next Steps" or architecture diagrams, explicitly show how your AI engine would sit *alongside* their current EKTIS integration, ensuring that the "Advice" layer never corrupts the "Legal Data" layer.