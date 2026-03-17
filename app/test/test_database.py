from flask import render_template, redirect, url_for, request, flash
from . import test_bp
from app.tasks import test_remote_db
from celery.result import AsyncResult

@test_bp.route('/testtask', methods=['GET', 'POST'])
def test_task():
    if request.method == 'POST':
        testtag = request.form['test_db_connection']
        print(f"\n\n\nTest Tag: {testtag}\n\n\n")
        flash(f"Test Tag: {testtag}" , "info")

    return render_template('test_page.html')


def get_result(id:str) -> dict[str, object]:
    result  = AsyncResult(id)
    ready   = result.ready()
    return {
        "ready"         :   ready,
        "successful"    :   result.successful() if ready else None,
        "value"         :   result.get() if ready else result.result,
    }


@test_bp.route('/test_remote_db', methods=['GET', 'POST'])
def connect_remote_db():
    if request.method == 'POST':
        task = test_remote_db.test_remote_db_connection.delay()
        # print(f"\n\nRemote DB connection test started. Task ID: [{task.id}] \n\n")
        # flash(f"Remote DB connection test started. Task ID: {task.id}", "info")
        
        # result = get_result(task.id)
        result = task.get(timeout=10)

        print(f"\n\n{result}\n\n")
        if result.success:
            print(f"\n\n {result} \n\n")
            flash(f"Remote DB connection test started. Task ID: {task.id}", "info")
            flash(f"Task Val: {result}", "info")
        else:
            flash(f"Remote DB connection test stopped. Task ID: {task.id}", "danger")

        return redirect(url_for("test_bp.test_task"))

    return render_template('test_page.html')


# -------------------------------------------------------------
# @test_bp.route("/test_index")
# def test_index():
#     return render_template('test_index.html')

# @test_bp.get("/result/<id>")
# def result(id: str) -> dict[str, object]:
#     result  = AsyncResult(id)
#     ready   = result.ready()
#     return {
#         "ready"         :   ready,
#         "successful"    :   result.successful() if ready else None,
#         "value"         :   result.get() if ready else result.result,
#     }

# @test_bp.post("/add")
# def add() -> dict[str, object]:
#     a = request.form.get("a", type=int)
#     b = request.form.get("b", type=int)
#     result = test_remote_db.add.delay(a, b)
#     return {"result_id": result.id}

# @test_bp.post("/block")
# def block() -> dict[str, object]:
#     result = test_remote_db.block.delay()
#     return {"result_id": result.id}

# @test_bp.post("/process")
# def process() -> dict[str, object]:
#     result = test_remote_db.process.delay(total=request.form.get("total", type=int))
#     return {"result_id": result.id}
