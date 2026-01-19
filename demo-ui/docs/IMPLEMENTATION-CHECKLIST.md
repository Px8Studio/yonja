# 🛠️ ALEM Persona Persistence — Implementation Checklist

**Goal:** Make personas persist across browser refresh + display in UI  
**Status:** Phase 1 & 2 ready for implementation  
**Estimated Time:** 2-3 hours  

---

## 📋 Implementation Checklist

### TIER 1: Database Persistence

#### Step 1.1: Create Alembic Migration
**File:** `alembic/versions/add_alem_personas_table.py`

```python
"""Add ALEM_Persona table for persona persistence

Revision ID: add_alem_personas_001
Revises: chainlit_tables_001
Create Date: 2026-01-19
"""
from alembic import op
import sqlalchemy as sa

revision = 'add_alem_personas_001'
down_revision = 'chainlit_tables_001'

def upgrade():
    op.create_table(
        'alem_personas',
        sa.Column('alem_persona_id', sa.String(36), nullable=False, comment='UUID primary key'),
        sa.Column('chainlit_user_id', sa.String(36), nullable=False, comment='FK to users.id'),
        sa.Column('email', sa.String(255), nullable=False, unique=True, comment='User email (from OAuth)'),
        sa.Column('user_profile_id', sa.String(20), nullable=True, comment='FK to user_profiles.user_id'),
        
        # Persona Data
        sa.Column('full_name', sa.String(100), nullable=False),
        sa.Column('fin_code', sa.String(20), nullable=True, unique=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('region', sa.String(50), nullable=False),
        sa.Column('crop_type', sa.String(50), nullable=False),
        sa.Column('total_area_ha', sa.Float(), nullable=False),
        sa.Column('experience_level', sa.String(20), nullable=True),
        sa.Column('ektis_verified', sa.Boolean(), default=False),
        
        # Metadata
        sa.Column('data_source', sa.String(20), default='synthetic', comment='synthetic/oauth/mygov'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        
        sa.PrimaryKeyConstraint('alem_persona_id'),
        sa.ForeignKeyConstraint(['chainlit_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_profile_id'], ['user_profiles.user_id'], ondelete='SET NULL'),
    )
    op.create_index('idx_alem_personas_email', 'alem_personas', ['email'], unique=True)
    op.create_index('idx_alem_personas_user_profile_id', 'alem_personas', ['user_profile_id'])

def downgrade():
    op.drop_table('alem_personas')
```

**To run:**
```bash
cd c:\Users\rjjaf\_Projects\yonja
alembic upgrade head
```

---

#### Step 1.2: Create SQLAlchemy Model
**File:** `src/yonca/data/models/alem_persona.py` (NEW)

```python
"""ALEM Persona database model."""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from yonca.data.database import Base

class ALEMPersonaDB(Base):
    """ALEM Persona ORM model for database persistence."""
    __tablename__ = 'alem_personas'
    
    alem_persona_id = Column(String(36), primary_key=True)
    chainlit_user_id = Column(String(36), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    user_profile_id = Column(String(20), ForeignKey('user_profiles.user_id', ondelete='SET NULL'), nullable=True, index=True)
    
    # Persona Data
    full_name = Column(String(100), nullable=False)
    fin_code = Column(String(20), nullable=True, unique=True)
    phone = Column(String(20), nullable=True)
    region = Column(String(50), nullable=False)
    crop_type = Column(String(50), nullable=False)
    total_area_ha = Column(Float(), nullable=False)
    experience_level = Column(String(20), nullable=True)
    ektis_verified = Column(Boolean(), default=False)
    
    # Metadata
    data_source = Column(String(20), default='synthetic')
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    def to_dict(self):
        """Convert to dictionary for session storage."""
        return {
            'alem_persona_id': self.alem_persona_id,
            'user_id': self.chainlit_user_id,
            'email': self.email,
            'full_name': self.full_name,
            'fin_code': self.fin_code,
            'phone': self.phone,
            'region': self.region,
            'crop_type': self.crop_type,
            'total_area_ha': self.total_area_ha,
            'experience_level': self.experience_level,
            'ektis_verified': self.ektis_verified,
            'data_source': self.data_source,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
        }
```

---

#### Step 1.3: Create Database Async Functions
**File:** `demo-ui/alem_persona_db.py` (NEW)

```python
"""Database persistence functions for ALEM Personas."""
import uuid
from datetime import datetime
from typing import Optional
import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from yonca.data.database import get_db_session

logger = structlog.get_logger(__name__)

async def load_alem_persona_from_db(
    email: str,
) -> Optional[dict]:
    """Load persona from database by email."""
    try:
        async with get_db_session() as session:
            result = await session.execute(
                text("""
                    SELECT alem_persona_id, email, full_name, fin_code, phone, 
                           region, crop_type, total_area_ha, experience_level, 
                           ektis_verified, data_source, created_at, last_login_at
                    FROM alem_personas
                    WHERE email = :email
                """),
                {"email": email}
            )
            row = result.fetchone()
            
            if row:
                logger.info("persona_loaded_from_db", email=email)
                return {
                    'alem_persona_id': row[0],
                    'email': row[1],
                    'full_name': row[2],
                    'fin_code': row[3],
                    'phone': row[4],
                    'region': row[5],
                    'crop_type': row[6],
                    'total_area_ha': row[7],
                    'experience_level': row[8],
                    'ektis_verified': row[9],
                    'data_source': row[10],
                    'created_at': row[11].isoformat() if row[11] else None,
                    'last_login_at': row[12].isoformat() if row[12] else None,
                }
            else:
                logger.debug("persona_not_found_in_db", email=email)
                return None
                
    except Exception as e:
        logger.error("load_persona_failed", email=email, error=str(e))
        return None


async def save_alem_persona_to_db(
    alem_persona: dict,
    chainlit_user_id: str,
    email: str,
    user_profile_id: Optional[str] = None,
) -> bool:
    """Save generated persona to database for persistence."""
    try:
        async with get_db_session() as session:
            persona_id = str(uuid.uuid4())
            
            await session.execute(
                text("""
                    INSERT INTO alem_personas (
                        alem_persona_id, chainlit_user_id, email, user_profile_id,
                        full_name, fin_code, phone, region, crop_type, total_area_ha,
                        experience_level, ektis_verified, data_source, created_at, last_login_at
                    ) VALUES (
                        :persona_id, :user_id, :email, :profile_id,
                        :name, :fin, :phone, :region, :crop, :area,
                        :exp, :verified, :source, :created, :login
                    )
                    ON CONFLICT (email) DO UPDATE SET
                        last_login_at = :login,
                        updated_at = CURRENT_TIMESTAMP
                """),
                {
                    'persona_id': persona_id,
                    'user_id': chainlit_user_id,
                    'email': email,
                    'profile_id': user_profile_id,
                    'name': alem_persona['full_name'],
                    'fin': alem_persona['fin_code'],
                    'phone': alem_persona['phone'],
                    'region': alem_persona['region'],
                    'crop': alem_persona['crop_type'],
                    'area': alem_persona['total_area_ha'],
                    'exp': alem_persona['experience_level'],
                    'verified': alem_persona.get('ektis_verified', False),
                    'source': alem_persona.get('data_source', 'synthetic'),
                    'created': datetime.utcnow(),
                    'login': datetime.utcnow(),
                }
            )
            logger.info("persona_saved_to_db", email=email, persona_id=persona_id)
            return True
            
    except Exception as e:
        logger.error("save_persona_failed", email=email, error=str(e))
        return False
```

---

#### Step 1.4: Integrate Persistence into app.py
**File:** `demo-ui/app.py` — Update `@on_chat_start`

**Add at top (imports):**
```python
from alem_persona_db import load_alem_persona_from_db, save_alem_persona_to_db
```

**Replace the JIT provisioning section (around line 978-1000):**
```python
# ─────────────────────────────────────────────────────────────
# JIT PERSONA PROVISIONING — Load from DB or generate new
# ─────────────────────────────────────────────────────────────
alem_persona: Optional[ALEMPersona] = None

if user and user.metadata:
    user_email = user.metadata.get("email")
    
    # TIER 1: Try to load from database (persistent)
    persona_dict = await load_alem_persona_from_db(user_email)
    
    if persona_dict:
        # ✅ Found in database - use it
        alem_persona = ALEMPersona(
            user_id=user.identifier,
            full_name=persona_dict['full_name'],
            email=persona_dict['email'],
            fin_code=persona_dict['fin_code'],
            phone=persona_dict['phone'],
            region=persona_dict['region'],
            crop_type=persona_dict['crop_type'],
            total_area_ha=persona_dict['total_area_ha'],
            experience_level=persona_dict['experience_level'],
            ektis_verified=persona_dict['ektis_verified'],
        )
        logger.info("persona_loaded_from_persistence", user_id=user.identifier)
    else:
        # ❌ Not in database - generate new one
        oauth_claims = {
            "name": user.metadata.get("name", "Unknown Farmer"),
            "email": user_email,
        }
        alem_persona = PersonaProvisioner.provision_from_oauth(
            user_id=user.identifier,
            oauth_claims=oauth_claims,
            existing_persona=None,
        )
        
        # Save to database for next time
        await save_alem_persona_to_db(
            alem_persona=alem_persona.to_dict(),
            chainlit_user_id=user.identifier,
            email=user_email,
        )
        logger.info("persona_generated_and_saved", user_id=user.identifier)
    
    # Store in session for this conversation
    cl.user_session.set("alem_persona", alem_persona.to_dict())
```

---

### TIER 2: Sidebar Display

#### Step 2.1: Create Sidebar Component
**File:** `demo-ui/app.py` — Add after persona is loaded (around line 1010)

```python
# ─────────────────────────────────────────────────────────────
# DISPLAY PERSONA IN CHAINLIT SIDEBAR
# ─────────────────────────────────────────────────────────────
if alem_persona:
    # Create sidebar element showing persona
    persona_display = alem_persona.to_sidebar_display()
    
    sidebar_element = cl.Markdown(
        content=f"""
### 🔐 ALEM Təsdiqlənmiş Profil

{persona_display}

---

**Mənbə:** {'Sintetik Demo' if alem_persona.ektis_verified == False else 'Hökumət Verilişi'}
""",
        display="side"
    )
    await sidebar_element.send()
    
    logger.info(
        "persona_displayed_in_sidebar",
        user_id=user_id,
        fin_code=alem_persona.fin_code,
    )
```

---

#### Step 2.2: Update Persona Display Method
**File:** `demo-ui/alem_persona.py` — Already exists, verify:

The `to_sidebar_display()` method should look like:
```python
def to_sidebar_display(self) -> str:
    """Format persona for Chainlit sidebar display."""
    return f"""
**FIN Kodu:** `{self.fin_code}`  
**Bölgə:** {self.region}  
**Məhsul:** {self.crop_type}  
**Sahə:** {self.total_area_ha} ha  
**Təcrübə:** {self.experience_level}  
**Təsdiqlənmiş:** {'✅ Bəli' if self.ektis_verified else '⏳ Demo'}
"""
```

---

### TIER 3: Verify It Works

#### Step 3.1: Run Migration
```bash
cd c:\Users\rjjaf\_Projects\yonja

# Run migration to create table
alembic upgrade head

# Verify table was created
psql -h localhost -p 5433 -U yonca -d yonca -c "SELECT * FROM alem_personas;"
# (should return empty, which is correct)
```

#### Step 3.2: Test Flow
1. **Start all services:**
   ```bash
   # Docker
   docker-compose -f docker-compose.local.yml up -d
   
   # LangGraph
   # UI
   ```

2. **Login with Google** → Should provision persona

3. **Check database:**
   ```bash
   psql -h localhost -p 5433 -U yonca -d yonca -c """
   SELECT email, fin_code, region, crop_type, data_source 
   FROM alem_personas 
   LIMIT 5;
   """
   ```
   Should show your persona!

4. **Refresh browser (F5)** → Persona should still be there (loaded from DB)

5. **Check sidebar** → Should show persona display

---

## 📊 What Happens After Implementation

### Before (Current)
```
Login → Generate persona → Store in session
         ↓
         Message to LangGraph
         ↓
Refresh browser → Persona LOST ❌
```

### After (With Persistence)
```
Login → Check database
         ↓
If exists: Load from DB ✅
If not: Generate new → Save to DB ✅
         ↓
Store in session
         ↓
Message to LangGraph
         ↓
Refresh browser → Reload from DB ✅
```

---

## 🔍 Verification Queries

### Check if persona table exists
```sql
SELECT * FROM information_schema.tables 
WHERE table_name = 'alem_personas';
```

### See all personas
```sql
SELECT email, fin_code, region, crop_type, data_source, created_at 
FROM alem_personas;
```

### See persona for specific user
```sql
SELECT * FROM alem_personas 
WHERE email = 'your-email@example.com';
```

### Update persona (if needed)
```sql
UPDATE alem_personas 
SET region = 'Quba', crop_type = 'Alma' 
WHERE email = 'your-email@example.com';
```

---

## 🐛 Debugging

### Issue: "Can't see persona after refresh"
**Check:**
1. Is `alem_personas` table created?
   ```sql
   \dt alem_personas  -- in psql
   ```

2. Is persona being saved?
   ```sql
   SELECT * FROM alem_personas WHERE email = 'your-email@example.com';
   ```

3. Are logs showing save/load?
   ```bash
   # Check Chainlit output for: "persona_saved_to_db" or "persona_loaded_from_persistence"
   ```

### Issue: "Getting duplicate key error"
**Reason:** FIN code or email already exists  
**Fix:**
```sql
-- Find duplicate
SELECT fin_code, COUNT(*) FROM alem_personas GROUP BY fin_code HAVING COUNT(*) > 1;

-- Delete old persona for same email
DELETE FROM alem_personas WHERE email = 'test@example.com' AND created_at < NOW() - INTERVAL '1 hour';
```

---

## 📝 Files to Create/Modify

| File | Action | Lines | Effort |
|------|--------|-------|--------|
| `alembic/versions/add_alem_personas_table.py` | CREATE | 40 | 15 min |
| `src/yonca/data/models/alem_persona.py` | CREATE | 50 | 10 min |
| `demo-ui/alem_persona_db.py` | CREATE | 100 | 20 min |
| `demo-ui/app.py` | MODIFY | +30 lines | 15 min |
| **Total** | | | **60 min** |

---

## ✅ Checklist

- [ ] Create migration file
- [ ] Create SQLAlchemy model
- [ ] Create async DB functions
- [ ] Update app.py imports
- [ ] Update @on_chat_start logic
- [ ] Add sidebar display
- [ ] Run migration (`alembic upgrade head`)
- [ ] Test login flow
- [ ] Test browser refresh
- [ ] Test sidebar display
- [ ] Verify personas in DB
