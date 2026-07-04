from app.handlers.admin import router as admin_router
from app.handlers.students import router as students_router
from app.handlers.student import router as student_router


routers = [
    admin_router,
    students_router,
    student_router,
]
