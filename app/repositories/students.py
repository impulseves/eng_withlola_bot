from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Payment, Student


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
    period_weeks: int,
) -> Student | None:
    student = session.get(Student, student_id)

    if not student:
        return None

    student.amount = amount
    student.payment_date = payment_date
    student.period_weeks = period_weeks
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

from calendar import monthrange
from datetime import date, datetime, timedelta


def confirm_payment(session: Session, student_id: int) -> Student | None:
    student = session.get(Student, student_id)

    if not student or not student.payment_date or not student.amount:
        return None

    payment = Payment(
        student_id=student.id,
        amount=student.amount,
        due_date=student.payment_date,
        status="confirmed",
    )

    session.add(payment)

    student.last_payment_date = student.payment_date
    student.payment_date = (
        student.payment_date +
        timedelta(weeks=student.period_weeks)
)

    student.payment_pending = False

    session.commit()
    session.refresh(student)

    return student

def get_pending_payments(session: Session) -> list[Student]:
    stmt = (
        select(Student)
        .where(Student.payment_pending == True)  # noqa: E712
        .where(Student.active == True)  # noqa: E712
        .order_by(Student.payment_date)
    )

    return list(session.scalars(stmt).all())

def reject_payment(session: Session, student_id: int) -> Student | None:
    student = session.get(Student, student_id)

    if not student:
        return None

    student.payment_pending = False

    session.commit()
    session.refresh(student)

    return student

from datetime import date


def get_all_students(session: Session) -> list[Student]:
    stmt = select(Student).order_by(Student.created_at.desc())
    return list(session.scalars(stmt).all())


def get_overdue_students(session: Session) -> list[Student]:
    today = date.today()

    stmt = (
        select(Student)
        .where(Student.active == True)  # noqa: E712
        .where(Student.payment_date < today)
        .order_by(Student.payment_date)
    )

    return list(session.scalars(stmt).all())

def get_student_payments(session: Session, student_id: int) -> list[Payment]:
    stmt = (
        select(Payment)
        .where(Payment.student_id == student_id)
        .order_by(Payment.confirmed_at.desc())
    )

    return list(session.scalars(stmt).all())

def get_by_id(session: Session, student_id: int) -> Student | None:
    return session.get(Student, student_id)

def update_student_amount(session: Session, student_id: int, amount: int) -> Student | None:
    student = session.get(Student, student_id)

    if not student:
        return None

    student.amount = amount
    session.commit()
    session.refresh(student)

    return student


def update_student_payment_date(session: Session, student_id: int, payment_date: date) -> Student | None:
    student = session.get(Student, student_id)

    if not student:
        return None

    student.payment_date = payment_date
    session.commit()
    session.refresh(student)

    return student


def update_student_period(session: Session, student_id: int, period_weeks: int) -> Student | None:
    student = session.get(Student, student_id)

    if not student:
        return None

    student.period_weeks = period_weeks
    session.commit()
    session.refresh(student)

    return student
