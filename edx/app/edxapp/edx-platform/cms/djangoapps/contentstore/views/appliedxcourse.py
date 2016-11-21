from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, Http404
from .library import LIBRARIES_ENABLED
from xmodule.modulestore.django import modulestore
from student.auth import has_course_author_access, has_studio_write_access, has_studio_read_access
from course_action_state.models import CourseRerunState, CourseRerunUIStateManager
from django.shortcuts import render_to_response
from student.roles import CourseInstructorRole, CourseStaffRole, LibraryUserRole
from opaque_keys.edx.keys import CourseKey, UsageKey
from opaque_keys import InvalidKeyError
from django.contrib.auth.models import User
from student.models import CourseEnrollment
from django.contrib.auth import authenticate
from django.core.mail import EmailMessage
from django.contrib.auth.views import login

def index(request):
	user = authenticate(username = "django20", password = "123456+")
	if user is not None:
    		request.user = user
	else:
		request.user = None
    			
	if LIBRARIES_ENABLED:
		courses, in_process_course_actions = get_courses_accessible_to_user(request)
		if len(courses) > 0:
			response = "<div><font color='blue'>"
			responsedisplay =''
			for course_info in courses:
				try:    	
    					course_key = CourseKey.from_string(str(course_info.id))
				except InvalidKeyError:
    					course_key = ''        	        		

    				course_module = modulestore().get_course(course_key)
				instructors = set(CourseInstructorRole(course_key).users_with_role())
				staff = set(CourseStaffRole(course_key).users_with_role()).union(instructors)
				
				formatted_users = []

    				for user in instructors:
  					response  += "<div>Dear "+str(user.first_name) +",<br/>Since Launch</div>"
					response  += "<br /> Course name	:"+ str(course_info.display_name)				
					courseEnv =  CourseEnrollment.objects.enrollment_counts(course_key)
					response  += "<div><font color='red'><font size='4'><b>"+ str(courseEnv['total']) +"</b></font></font> people have enrolled in your course, <br /> --- of them Completed it"+"</div>"	
					response += "<div>" +"Student map location for your course :<b>"+  """<a href=" http://35.162.171.46:18010/coursereport/""" + str(course_key) + """ "> """ + str(course_info.display_name) + "</a></b> <br/>" +"</div>"
					response  +="</div>"
					
					email = EmailMessage('Course List', response, to= [user.email])
					email.content_subtype = 'html'
					email.send()
					responsedisplay += response
					response = ''
				for user in staff - instructors:
  					response  += "<div>Dear "+str(user.first_name) +", <br/>Since Launch</div>"
					response  += "<br /> Course name	:"+ str(course_info.display_name)
					courseEnv =  CourseEnrollment.objects.enrollment_counts(course_key)
					response  += "<div><font color='red'><font size='4'><b>"+ str(courseEnv['total']) +"</b></font></font> people have enrolled in your course, <br /> --- of them Completed it"+"</div>"	
					response += "<div>" +"Student map location for your course :<b>"+  """<a href=" http://35.162.171.46:18010/coursereport/""" + str(course_key) + """ "> """ + str(course_info.display_name) + "</a> </b> <br/>" +"</div>"					

					response  +="</div><br /><br />"
					email = EmailMessage('Course Report', response, to= [user.email])					
					email.content_subtype = 'html'
					email.send()
					responsedisplay += response							
					response = ''

			return HttpResponse(responsedisplay)
		else:
			return HttpResponse("No course found")
	else:
   		return HttpResponse("Library not enabled")



def get_courses_accessible_to_user(request):
    courses, in_process_course_actions = _accessible_courses_summary_list(request)
    return courses, in_process_course_actions

def _accessible_courses_summary_list(request):	
    courses_summary = filter(course_filter, modulestore().get_course_summaries())
    in_process_course_actions = get_in_process_course_actions(request)
    return courses_summary, in_process_course_actions

def get_in_process_course_actions(request):
    """
     Get all in-process course actions
    """
    return [
        course for course in
        CourseRerunState.objects.find_all(
            exclude_args={'state': CourseRerunUIStateManager.State.SUCCEEDED}, should_display=True
        )
        if has_studio_read_access(request.user, course.course_key)
    ]

def _accessible_courses_summary_list(request):
    """
    List all courses available to the logged in user by iterating through all the courses
    """
    def course_filter(course_summary):
        """
        Filter out unusable and inaccessible courses
        """
        # pylint: disable=fixme
        # TODO remove this condition when templates purged from db
        if course_summary.location.course == 'templates':
            return False

        return has_studio_read_access(request.user, course_summary.id)

    courses_summary = filter(course_filter, modulestore().get_course_summaries())
    in_process_course_actions = get_in_process_course_actions(request)
    return courses_summary, in_process_course_actions

def user_with_role(user, role):
    """ Build user representation with attached role """
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': role
    }