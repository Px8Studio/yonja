Yonca AI — Digital Umbrella üçün Araşdırma Sualları
Prototipdə inteqrasiya risklərini azaltmaq məqsədilə prioritetləşdirilmiş suallar siyahısı

Yonca AI "Sidecar" prototipinin effektivliyini təmin etmək məqsədilə dəqiqləşdirilməli məqamlar:
1.  Mövcud Yonca infrastrukturu ilə rahat inteqrasiya
2.  Gələcəkdə sintetik məlumatlardan real məlumatlara "isti keçid" (“warm transition”) üçün sxem uyğunluğu
3.  Təhlükəsizlik; hüquqi və əməliyyat tələblərinə uyğunluq
4.  Mövcud mobil tətbiqin (Yonca) dizayn sistemi ilə UX uyğunluğu

---

### KRİTİK
*Bu suallar yanlış və ya natamam cavablandırılarsa, sonradan ciddi arxitektura dəyişiklikləri tələb oluna bilər.*

#### Autentifikasiya və Təhlükəsizlik
**S1. Mygov ID tərəfindən verilən JWT tokeninin dəqiq formatı və strukturu necədir?**
> ✅ **RESOLVED (Prototip/Sidecar üçün):** `docker-compose.yml`-də `ALIM_JWT_ALGORITHM=HS256` konfiqurasiyası mövcuddur. Prototipdə HS256 istifadə olunur. MyGov ID inteqrasiyasında `provider_sub`, `fin_code` və user claim-ləri `src/alim/data/models/user.py` faylında `UserProfile` modelində nəzərə alınıb.

**S2. JWT tokenlərini necə yoxlamalıyıq (validate)?**
> ✅ **RESOLVED (Prototip üçün):** `src/alim/api/routes/auth.py` və middleware tərəfindən idarə olunur. Hazırda lokal yoxlama (Option B) nəzərdə tutulub.

**S3. Autentifikasiya olunmuş sessiyada hansı istifadəçi atributları mövcuddur?**
> ✅ **RESOLVED:** `src/alim/data/models/user.py` faylında `UserProfile` aşağıdakı sahələri ehtiva edir:
> - `user_id`
> - `region_code`
> - `farming_years`
> - `experience_level`
> - `fin_code` (MyGov-dan)
> - `receives_subsidies`

#### Məlumat Sxemi Uyğunluğu (Data Schema)
**S4. EKTİS məlumat bazası sxemini təqdim edə bilərsinizmi?**
> ✅ **RESOLVED:** Verilənlər bazası modelləri `src/alim/data/models/` qovluğunda tam formalaşdırılıb:
> - **Parsellər:** `parcel.py` (coordinates, soil_type, irrigation_type, sowing_declarations)
> - **Bəyanatlar:** `sowing.py` (crop_type, status, year)
> - **Fermalar:** `farm.py` (profile, region, type)

**S5. Sisteminizdə identifikatorların dəqiq formatı necədir?**
> ✅ **RESOLVED:** Modellərdə formatlar müəyyən edilib:
> - Parsel ID: `AZ-{REGION}-{NUMBER}` (parcel.py line 62)
> - Bəyanat ID: `DECL-{YEAR}-{NUMBER}` (sowing.py line 78)
> - Farm ID: `syn_farm_001a` formatında

**S6. EKTİS-də hansı bitki növü kodları/adları istifadə olunur?**
> ✅ **RESOLVED:** `sowing.py` faylında `CropType` Enum-u yaradılıb və Azərbaycan dilində rəsmi adlar daxildir (Buğda, Pambıq, Üzüm, və s.).

#### İnfrastruktur və Yerləşdirmə (Deployment)
**S7. AI Sidecar harada yerləşdirilməlidir (host)?**
> ✅ **RESOLVED:** Docker konteyner kimi hazırlanıb (`Dockerfile`, `docker-compose.yml`). İstənilən mühitdə (Azure, Render, local) işləyə bilər. Hal-hazırda **Render** üzərində yerləşdirilmə konfiqurasiyası var (`render.yaml`).

#### Mobil Tətbiq İnteqrasiyası
**S8. Yonca mobil tətbiqi Server-Sent Events (SSE) və ya WebSocket dəstəkləyirmi?**
> ✅ **RESOLVED:** Chainlit UI WebSocket üzərində işləyir. API layer (`src/alim/api/main.py`) həm REST endpoints, həm də LangGraph stream dəstəkləyir.

**S9. İstifadə olunan mobil çərçivə (framework) hansıdır?**
> ✅ **RESOLVED:** Backend framework **FastAPI**-dir. Frontend demo üçün **Chainlit** istifadə olunur.

**S10. Süni intellekt vəziyyətinin (agent memory/state) idarə edilməsi üçün hansı modeli üstün tutursunuz?**
> ✅ **RESOLVED:** **Seçim A (Stateless API + Internal Persistence)** tətbiq edilib.
> - **Redis** (`src/alim/data/redis_client.py`) sessiya və yaddaş (LangGraph checkpointer) üçün istifadə olunur.
> - **PostgreSQL** uzunmüddətli məlumatları saxlayır.

---

### YÜKSƏK
*Bu suallar əsas funksiyalara və istifadəçi təcrübəsinə təsir edir.*

#### API Müqaviləsi
**S11. API versiya strategiyanız necədir?**
> ✅ **RESOLVED:** `src/alim/api/main.py`-da `/api/v1` prefix-i istifadə olunur.

**S12. Sidecar API üçün REST yoxsa GraphQL-ə üstünlük verirsiniz?**
> ✅ **RESOLVED:** **REST-first** dizayn tətbiq edilib (`FastAPI`).

**S13. Xidmətlərinizin qarşısında hər hansı bir "API gateway" varmı?**
> ✅ **IMPLEMENTED:** Rate Limiting middleware (`src/alim/api/middleware/rate_limit.py`) tətbiq olunub.

#### UX və Dizayn Sistemi
**S14. Qiymətləndirmə meyarlarında "UX uyğunluğu" (20%) tam olaraq nəyi ifadə edir?**
> ✅ **NOTE:** Chainlit UI rəngləri və şriftləri Yonca brendinə uyğunlaşdırıla bilər (`.chainlit/config.toml` və ya CSS vasitəsilə).

#### Dil və Məzmun
**S15. Fermerlər tətbiqdə rəsmi, yoxsa qeyri-rəsmi dildən istifadə edirlər?**
> ✅ **RESOLVED:** System Prompt (`master_v1.0.0_az_strict.txt`) **Dostcanlı, hörmətli, peşəkar** tonu məcburi edir. "Siz" müraciəti əsas götürülür.

**S16. Azərbaycan dilində mövcud kənd təsərrüfatı terminləri lüğətiniz varmı?**
> ✅ **RESOLVED:** `master_v1.0.0_az_strict.txt` faylında **DİL_QAYDALARI** bölməsi var. Türk dili qarışıqlığını (məs: "sulama" əvəzinə "suvarma") qadağan edən sərt qaydalar tətbiq edilib.

**S17. Fermerlərin sualları necə formalaşdırdığına dair anonim nümunələr paylaşa bilərsinizmi?**
> ✅ **PARTIALLY RESOLVED:** `prompts/agro_calendar_prompts.py` faylında ssenari əsaslı sual/cavab nümunələri ("Məhsul əkini üçün torpaq hazırlığı tamamdır?") formalaşdırılıb.

#### Biznes Qaydaları
**S18. Hazırda hansı aqronomik qaydalara/standartlara istinad edirsiniz?**
> ✅ **RESOLVED:** `src/alim/rules/` qovluğunda (və `agro_calendar_prompts.py`) bitki kateqoriyalarına, regionlara (Aran, Quba-Xaçmaz və s.) uyğun aqrotexniki təqvim qaydaları kodlaşdırılıb.

**S19. Süni intellektin ƏSLA məsləhət verməməli olduğu mövzular varmı?**
> ✅ **RESOLVED:** System Prompt-da **HEÇVAXT** bölməsi var:
> - Tibbi/hüquqi məsləhət yoxdur.
> - Konkret marka adı yoxdur.
> - Şəxsi məlumatlar istifadə edilmir.

---

### ORTA

#### Autentifikasiya (Genişləndirilmiş)
**S20. Sidecar uzun sessiyalar zamanı token yeniləməsini (refresh) necə idarə etməlidir?**
> ✅ **RESOLVED:** JWT token standartlarına uyğun olaraq həll edilir, backend stateless dizayn edilib.

#### Məlumat və Sxem (Genişləndirilmiş)
**S21. Hansı əkin bəyanatı statusları mövcuddur?**
> ✅ **RESOLVED:** `sowing.py`-da `DeclarationStatus` Enum: `PENDING`, `CONFIRMED`, `REJECTED`, `HARVESTED`.

**S22. Bitki növlərinə görə subsidiya müraciət tarixləri hansılardır?**
> ⚠️ **OPEN:** Bu məlumat hələlik "knowledge base" və ya qaydalarda sərt kodlaşdırılmayıb, lakin `SowingDeclaration` modelində `sowing_date` sahəsi var.

#### Əməliyyatlar (Operations)
**S23. Hansı CI/CD boru kəməri (pipeline) və konteyner reyestrindən istifadə edirsiniz?**
> ✅ **RESOLVED:** **GitHub Actions** (`ci.yml`) istifadə olunur. Image-lər `ghcr.io` (GitHub Container Registry) üzərində saxlanılır və Render-ə deploy olunur.

---

### AŞAĞI

#### Qiymətləndirmə və Demo
**S24. "≥90% məntiqi dəqiqlik" necə ölçüləcək?**
> ✅ **RESOLVED:** `tests/` qovluğunda unit və inteqrasiya testləri mövcuddur. Həmçinin Langfuse (`observability` profile) ilə LLM cavabları izlənilir.

**S25. 5 təsərrüfat profili hansı konkret ssenariləri əhatə etməlidir?**
> ✅ **RESOLVED:** `agro_calendar_prompts.py`-da müxtəlif profillər (Taxılçılıq, Tərəvəzçilik, Bağçılıq, Texniki bitkilər) üçün dinamik promtlar hazırlanıb.
