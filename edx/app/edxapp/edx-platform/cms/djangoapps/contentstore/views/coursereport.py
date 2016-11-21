from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, Http404
from django.contrib.auth import authenticate
from django.contrib.auth.views import login
from edxmako.shortcuts import render_to_response
from opaque_keys.edx.keys import CourseKey, UsageKey
import instructor_analytics.distributions
import instructor_analytics.basic
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from collections import Counter

from django.shortcuts import render
import json

def index(request, course_key_string):
	user = authenticate(username = "django20", password = "123456+")
	if user is not None:
    		request.user = user
	else:
		request.user = None
    		return HttpResponse("Not Login")

	query_features = [
        	'country',
	]			
								
				
	response =""
	course_key = CourseKey.from_string(course_key_string)
   	student_data = instructor_analytics.basic.enrolled_students_features(course_key, query_features)
        stuList = []
	for student in student_data:					
		response += str(student['country'] + "<br/>")
		stuList.append(student['country'])	
			
	count = Counter(stuList)
	return render(request, 'course.html', {'report': json.dumps(count)})
