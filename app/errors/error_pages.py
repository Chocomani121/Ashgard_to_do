from flask import Blueprint, render_template, request

error_bp = Blueprint('error_bp', __name__, template_folder='err_templates')


# 400 - not found
@error_bp.app_errorhandler(400)
def error_400(error):
    if request.method == 'GET':
        error_status = 400
        error_msg = 'BAD REQUEST'
        error_desc = 'The server cannot process your request due to invalid or malformed input.'
        return render_template('pages-500.html', title = error_status, 
                                                error_status = error_status, 
                                                error_msg = error_msg,
                                                error_desc = error_desc), error_status

# 401 - (Unauthorized)
@error_bp.app_errorhandler(401)
def error_401(error):
    if request.method == 'GET':
        error_status = 401
        error_msg = 'UNAUTHORIZED'
        error_desc = 'Authentication is required, and you have not provided valid credentials.'
        return render_template('pages-500.html', title = error_status, 
                                                error_status = error_status, 
                                                error_msg = error_msg,
                                                error_desc = error_desc), error_status

# 403 - forbidden access
@error_bp.app_errorhandler(403)
def error_403(error):
    if request.method == 'GET':
        # return render_template('403_error.html', title='Error 403'), 403
        error_status = 403
        error_msg = 'FORBIDDEN'
        error_desc = 'You do not have permission to access this resource.'
        return render_template('pages-500.html', title = error_status, 
                                                error_status = error_status, 
                                                error_msg = error_msg,
                                                error_desc = error_desc), error_status

# 404 - not found
@error_bp.app_errorhandler(404)
def error_404(error):
    if request.method == 'GET':
        error_status = 404
        error_msg = 'PAGE NOT FOUND'
        error_desc = 'The requested page or resource could not be found on the server'
        return render_template('pages-500.html', title = error_status, 
                                                error_status = error_status, 
                                                error_msg = error_msg,
                                                error_desc = error_desc), error_status

# 405 - forbidden access
@error_bp.app_errorhandler(405)
def error_405(error):
    if request.method == 'GET':
        error_status = 405
        error_msg = 'METHOD NOT ALLOWED'
        error_desc = 'The request method used is not supported for this resource.'
        return render_template('pages-500.html', title = error_status, 
                                                error_status = error_status, 
                                                error_msg = error_msg,
                                                error_desc = error_desc), error_status

# 500 - server error
@error_bp.app_errorhandler(500)
def error_500(error):
    if request.method == 'GET':
        error_status = 500
        error_msg = 'INTERNAL SERVER ERROR'
        error_desc = 'The server encountered an unexpected condition that prevented it from fulfilling the request.'
        return render_template('pages-500.html', title = error_status, 
                                                error_status = error_status, 
                                                error_msg = error_msg,
                                                error_desc = error_desc), error_status



