from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Student


def get_by_telegram_id(session: Session, telegram_id: int) -> Student | None:
    stmt = select(Student).where(Student.telegram_id == telegram_id)
    return session.scalar(stmt)


def create_student(
    session: Session,
    telegram_id: int,
    name: str,
    username: str | None = None,
) -> Student:
    student = Student(
    telegram_id=telegram_id,
    name=name,
    username=username,
    approved=False,
    active=False,
    )

    session.add(student)
    session.commit()
    session.refresh(student)

    return student


def get_or_create_student(
    session: Session,
    telegram_id: int,
    name: str,
    username: str | None = None,
) -> tuple[Student, bool]:
    student = get_by_telegram_id(session, telegram_id)

    if student:
        return student, False

    student = create_student(
        session=session,
        telegram_id=telegram_id,
        name=name,
        username=username,
    )

    return student, True


def approve_student(
    session: Session,
    student_id: int,
    amount: int,
    payment_date: date,
    notes: str | None = None,
) -> Student | None:
    student = session.get(Student, student_id)

    if not student:
        return None

    student.amount = amount
    student.payment_date = payment_date
    student.notes = notes
    student.approved = True
    student.active = True

    session.commit()
    session.refresh(student)

    return student


def get_new_students(session: Session) -> list[Student]:
    stmt = (
        select(Student)
        .where(Student.approved == False) # noqa: E712
        .order_by(Student.created_at.desc())
    )

    return list(session.scalars(stmt).all())


def get_active_students(session: Session) -> list[Student]:
    stmt = (
        select(Student)
        .where(Student.approved == True) # noqa: E712
        .where(Student.active == True) # noqa: E712
        .order_by(Student.name)
    )

    return list(session.scalars(stmt).all())


def set_payment_pending(
    session: Session,
    student_id: int,
    value: bool = True,
) -> Student | None:
    student = session.get(Student, student_id)

    if not student:
        return None

    student.payment_pending = value

    session.commit()
    session.refresh(student)

    return student


def deactivate_student(session: Session, student_id: int) -> Student | None:
    student = session.get(Student, student_id)

    if not student:
        return None

    student.active = False

    session.commit()
    session.refresh(student)
    return student