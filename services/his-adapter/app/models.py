from sqlalchemy import Column, Integer, String, Float, SmallInteger, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from .database import Base

class ServiceMeasureUnit(Base):
    """Справочник единиц измерения (реальная таблица SERVICE_MEASURE_UNIT)."""
    __tablename__ = "SERVICE_MEASURE_UNIT"

    id = Column("ID", Integer, primary_key=True, index=True)
    code = Column("CODE", String(50))   # Код по ОКЕИ
    name = Column("NAME", String(100))  # Полное наименование (Грамм, Штука)
    alias = Column("ALIAS", String(20)) # Сокращение (г, шт)
    
    services = relationship("Service", back_populates="measure_unit")

class Service(Base):
    __tablename__ = "SERVICES"
    id = Column("ID", Integer, primary_key=True, index=True)
    name = Column("NAME", String(255), nullable=False)
    gtin = Column("GTIN", String(14))
    is_marked = Column("IS_MARKED", SmallInteger, default=0)
    rest = Column("REST", Float, default=0.0)
    store_id = Column("STORE_ID", Integer)
    
    # Ссылка на единицу измерения
    measure_unit_id = Column("MEAUSEREUNITID", Integer, ForeignKey("SERVICE_MEASURE_UNIT.ID"))
    # Возможность частичной продажи/выбытия
    is_allow_sale_in_parts = Column("ISALLOWSALEINPARTS", SmallInteger, default=0)

    measure_unit = relationship("ServiceMeasureUnit", back_populates="services")
    doc_rows = relationship("StoreDocTable", back_populates="service")

class Store(Base):
    __tablename__ = "STORES"
    id = Column("ID", Integer, primary_key=True, index=True)
    name = Column("NAME", String(255), nullable=False)

class StoreDoc(Base):
    __tablename__ = "STORE_DOC"
    id = Column("ID", Integer, primary_key=True, index=True)
    doctype_id = Column("DOCTYPEID", Integer)
    number = Column("NUMBER", String(50))
    date_fact = Column("DATEFACT", Integer)
    is_close = Column("ISCLOSE", SmallInteger, default=0)
    store_from = Column("STOREIDMK", Integer)
    store_to = Column("STOREIDCL", Integer)
    org_id = Column("ORGID", Integer, default=1)
    
    rows = relationship("StoreDocTable", back_populates="document")
    gis_meta = relationship("GisMtMetadata", back_populates="document", uselist=False)

class StoreDocTable(Base):
    __tablename__ = "STORE_DOC_TABLE"
    id = Column("ID", Integer, primary_key=True, index=True)
    doc_id = Column("DOCID", Integer, ForeignKey("STORE_DOC.ID"))
    service_id = Column("SERVICEID", Integer, ForeignKey("SERVICES.ID"))
    num = Column("NUM", Float)
    
    document = relationship("StoreDoc", back_populates="rows")
    service = relationship("Service", back_populates="doc_rows")
    sgtins = relationship("StoreDocTableSgtin", back_populates="doc_row")

class StoreDocTableSgtin(Base):
    """Связь строк документа с КИ с поддержкой частичного выбытия."""
    __tablename__ = "STORE_DOC_TABLE_SGTIN"
    id = Column("ID", Integer, primary_key=True, index=True)
    doc_table_id = Column("DOCTABLEID", Integer, ForeignKey("STORE_DOC_TABLE.ID"))
    sgtin = Column("SGTIN", String(150))
    
    # Поля для учета разукомплектации (частей упаковки)
    sold_part1 = Column("SOLDPART1", SmallInteger, default=1) # Текущая доля (числитель)
    sold_part2 = Column("SOLDPART2", SmallInteger, default=1) # Общий объем (знаменатель)

    doc_row = relationship("StoreDocTable", back_populates="sgtins")

class SgtinRegistry(Base):
    __tablename__ = "SGTIN_REGISTRY"
    id = Column("ID", Integer, primary_key=True, index=True)
    service_id = Column("SERVICE_ID", Integer, ForeignKey("SERVICES.ID"))
    sgtin = Column("SGTIN", String(150))
    status = Column("STATUS", String(50), default='AVAILABLE')
    service = relationship("Service")

class GisMtMetadata(Base):
    __tablename__ = "GIS_MT_METADATA"
    id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("STORE_DOC.ID"), unique=True, nullable=False)
    dropout_reason = Column(String(50), nullable=False)
    source_doc_type = Column(String(50), nullable=False)
    source_doc_date = Column(Date, nullable=False)
    source_doc_num = Column(String(50), nullable=False)
    source_doc_name = Column(String(255), nullable=True)
    saga_id = Column(String(100), nullable=True)
    gis_mt_status = Column(String(50), default="PENDING")
    gis_mt_errors = Column(Text, nullable=True)

    document = relationship("StoreDoc", back_populates="gis_meta")