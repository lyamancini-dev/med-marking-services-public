from sqlalchemy import update as sql_update
from sqlalchemy.orm import Session
from ..models import StoreDoc, StoreDocTable, Service, SgtinRegistry

def store_calc_doc(db: Session, doc_id: int):
    """Эмуляция системной процедуры МИС: закрытие документа и пересчёт остатков.
    Бросает ValueError при нарушении бизнес-правил.
    """
    doc = db.query(StoreDoc).filter(StoreDoc.id == doc_id).first()
    if not doc:
        raise ValueError("Документ не найден")
    if doc.is_close != 1:
        raise ValueError("Документ не закрыт (is_close != 1)")

    # 1. Валидация остатков перед проведением
    for row in doc.rows:
        if doc.doctype_id == 2:  # Списание
            service = db.query(Service).filter(
                Service.id == row.service_id,
                Service.store_id == doc.store_from
            ).first()
            if not service:
                raise ValueError(f"Товар ID={row.service_id} не найден на складе отправителя")
            if service.rest < row.num:
                raise ValueError(f"Недостаточно товара ID={row.service_id} на складе")
        elif doc.doctype_id == 3:  # Перемещение
            sender = db.query(Service).filter(
                Service.id == row.service_id,
                Service.store_id == doc.store_from
            ).first()
            if sender and sender.rest < row.num:
                raise ValueError(f"Недостаточно товара ID={row.service_id} на складе-отправителе")

    # 2. Пересчёт остатков
    for row in doc.rows:
        if doc.doctype_id == 2:  # Списание
            service = db.query(Service).filter(
                Service.id == row.service_id,
                Service.store_id == doc.store_from
            ).first()
            if service:
                service.rest -= row.num
                if service.rest <= 0:
                    db.delete(service)
        elif doc.doctype_id == 3:  # Перемещение
            # отправитель
            sender_srv = db.query(Service).filter(
                Service.id == row.service_id,
                Service.store_id == doc.store_from
            ).first()
            if sender_srv:
                sender_srv.rest -= row.num
                if sender_srv.rest <= 0:
                    db.delete(sender_srv)

            # получатель
            receiver_srv = db.query(Service).filter(
                Service.id == row.service_id,
                Service.store_id == doc.store_to
            ).first()
            if receiver_srv:
                receiver_srv.rest += row.num
            elif sender_srv:
                # Если товара ещё нет на складе-получателе, создаём запись
                new_item = Service(
                    name=sender_srv.name,
                    gtin=sender_srv.gtin,
                    is_marked=sender_srv.is_marked,
                    rest=row.num,
                    store_id=doc.store_to,
                    measure_unit_id=sender_srv.measure_unit_id,
                    is_allow_sale_in_parts=sender_srv.is_allow_sale_in_parts,
                )
                db.add(new_item)

    # 3. Обновление статусов КИ в реестре
    for row in doc.rows:
        sgtin_values = [s.sgtin for s in row.sgtins]
        if not sgtin_values:
            continue
        if doc.doctype_id == 2:
            new_status = 'WRITTEN_OFF'
        elif doc.doctype_id == 3:
            new_status = 'MOVED'
        else:
            continue
        stmt = (
            sql_update(SgtinRegistry)
            .where(
                SgtinRegistry.sgtin.in_(sgtin_values),
                SgtinRegistry.service_id == row.service_id
            )
            .values(status=new_status)
        )
        result = db.execute(stmt)
        print(f"Updated {result.rowcount} SGTIN(s) to {new_status}")

    db.commit()