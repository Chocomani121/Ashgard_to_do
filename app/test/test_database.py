from flask import render_template, redirect, url_for, request
from . import test_bp

@test_bp.route('/testtask', methods=['GET', 'POST'])
def test_task():
    return render_template('test_page.html')