from django.views.generic.detail import SingleObjectMixin
from django.views.generic import View, DetailView
from django.utils.decorators import method_decorator
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponseNotAllowed
from django.utils import simplejson as json

from django.contrib.auth.decorators import login_required

from voting.models import Vote



class RecordVoteOnItemView(SingleObjectMixin, View):
    """
    Records the vote casted by the current (authenticated) user on a given model instance.
    
    Note that this is an abstract view, intended to be subclassed in order to make a given 
    data model "votable". To do so, just set the ``model`` class attribute to the Django model'
    class whose instances have to be made votable.
    
    The model instance to be voted against is retrieved by the ``get_object()`` method. 
    The default implementation relies on the lookup logic provided by the built-in ``DetailView`` 
    view.
    
    After a (regular HTTP) vote request has been successfully processed, the view redirects 
    the client to the URL returned by the ``get_success_url()`` method.  
    The default implementation of  ``get_success_url()`` looks for the success URL 
    in the following places, in order:
      
      * the ``post_vote_redirect`` class attribute, if set 
      * the ``next`` parameter of the incoming HTTP request, if any
      * the ``get_absolute_url()`` method of the object returned by the ``get_object()`` method
   
   If this strategy doesn't fit your needs, just override ``get_success_url()`` in concrete subclass.
    
  If instead the vote request is performed via AJAX, a JSON object is returned to the client by the 
  ``get_json_response()`` method.  The default implementation build an object with the following properties:
    
     * ``success``: ``true`` if the vote was successfully registered, ``false`` otherwise
     * ``score``: an object having the properties ``score`` (the sum of all votes casted on the given object) 
       and ``num_votes`` (the number of votes casted on the given object)
     * ``error_message``: a message describing an error condition occurred while processing the vote 
    """
    model = None
    post_vote_redirect = None
    VOTE_DIRECTIONS = {'up': 1, 'down': -1, 'clear': 0}
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(RecordVoteOnItemView, self).dispatch(*args, **kwargs)
    
    def get_object(self):
        """
        Returns the object being voted upon.
        """
        return super(RecordVoteOnItemView, self).get_object()
    
    def get_success_url(self):
        """
        Returns the URL to redirect to if user's vote has been successfully registered.
        """
        if self.post_vote_redirect is not None:
            next = self.post_vote_redirect
        elif self.request.REQUEST.has_key('next'):
            next = self.request.REQUEST['next']
        elif hasattr(self.object, 'get_absolute_url') and callable(self.object.get_absolute_url):
            next = self.object.get_absolute_url()
        else:
            msg = """
                  Cannot find the URL where to redirect to after user's vote has been registered.
                  
                  Either: 
                    * add a 'post_vote_redirect' class attribute to this view
                    * specify a 'next' parameter in the request
                    * define a 'get_absolute_url()' method for the object being voted on 
                  """
            return HttpResponseBadRequest(msg)
        
        return next
          
    def get_json_response(self, err_msg=None):
        """
        Returns a JSON object suitable to be returned to the client. 
        """
        if err_msg is not None:
            data = json.dumps(dict(success=False, error_message=err_msg))
        else:
            data = json.dumps(dict(success=True, score=Vote.objects.get_score(self.object)))    
        return data

    def get(self, request, *args, **kwargs):
        msg = "Votes on %s objects can only be issued via POST" % self.model._meta.object_name
        return HttpResponseNotAllowed(msg)
    
    def post(self, request, *args, **kwargs):
        try:
            vote = self.VOTE_DIRECTIONS[self.kwargs['direction']]
        except KeyError:
            direction = self.kwargs.get('direction', None)
            if self.request.is_ajax():
                self.get_json_response(err_msg="\'%s\' is not a valid vote type." % direction)
            else:
                return HttpResponseBadRequest("'%s' is not a valid vote type." % direction)
        # the object being voted upon
        self.object = self.get_object()
        # record user-casted vote
        Vote.objects.record_vote(self.object, self.request.user, vote)
        if self.request.is_ajax():
            return HttpResponse(self.get_json_response())
        else:
            return HttpResponseRedirect(self.get_success_url())

        
class ConfirmVoteOnItemView(DetailView):
    """
    Display a confirmation message when a voting request has been successfully processed.
    
    When rendering the confirmation page, these template names will be tried, in order:
    
    * the string provided by the ``template_name`` class attribute, if present
     
    * ``<app label>/<model name>_<template_name_suffix>.html``, where:
    
        * ``<app label>`` and ``<model name>`` refer to the (required) ``model`` class attribute
        * ``<template_name_suffix>`` is the value (default: ``_confirm_vote``) of the  
          ``template_name_suffix`` class attribute
     
    This view adds the following variable to the template context:
    
    * ``object``: the object being voted upon.  You can change this default by overriding the 
      ``template_object_name`` class attribute
    * ``direction``: the vote's direction (one of 'up', 'down', 'clear')
    
    As usual, you can construct a different context by providing a custom implementation of the 
    ``get_context_data()`` method.
     """
    template_name = None
    template_name_suffix = '_confirm_vote'
    template_object_name='object'

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ConfirmVoteOnItemView, self).dispatch(*args, **kwargs)
    
    def get_context_data(self, **kwargs):
        # call the base implementation first to get a context
        context = super(ConfirmVoteOnItemView, self).get_context_data(**kwargs)
        context['direction'] = self.kwargs.get('direction')     
        return context
