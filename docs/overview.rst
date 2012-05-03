==============
Django Voting
==============

A generic voting application for Django projects, which allows
registering of votes for any ``Model`` instance.


Installation
============

Google Code recommends doing the Subversion checkout like so::

    svn checkout http://django-voting.googlecode.com/svn/trunk/ django-voting

But the hyphen in the application name can cause issues installing
into a DB, so it's really better to do this::

    svn checkout http://django-voting.googlecode.com/svn/trunk/ voting

If you've already downloaded, rename the directory before installing.

To install django-voting, do the following:

    1. Put the ``voting`` folder somewhere on your Python path.
    2. Put ``'voting'`` in your ``INSTALLED_APPS`` setting.
    3. Run the command ``manage.py syncdb``.

The ``syncdb`` command creates the necessary database tables and
creates permission objects for all installed apps that need them.

That's it!


Votes
=====

Votes are represented by the ``Vote`` model, which lives in the
``voting.models`` module.

API reference
-------------

Fields
~~~~~~

``Vote`` objects have the following fields:

    * ``user`` -- The user who made the vote. Users are represented by
      the ``django.contrib.auth.models.User`` model.
    * ``content_type`` -- The ContentType of the object voted on.
    * ``object_id`` -- The id of the object voted on.
    * ``object`` -- The object voted on.
    * ``vote`` -- The vote which was made: ``+1`` or ``-1``.

Methods
~~~~~~~

``Vote`` objects have the following custom methods:

    * ``is_upvote`` -- Returns ``True`` if ``vote`` is ``+1``.

    * ``is_downvote`` -- Returns ``True`` if ``vote`` is ``-1``.

Manager functions
~~~~~~~~~~~~~~~~~

The ``Vote`` model has a custom manager exposing the following helper
functions:

    * ``record_vote(obj, user, vote)`` -- Record a user's vote on a
      given object. Only allows a given user to vote once on any given
      object, but the vote may be changed.

      ``vote`` must be one of ``1`` (up vote), ``-1`` (down vote) or
      ``0`` (remove vote).

    * ``get_score(obj)`` -- Gets the total score for ``obj`` and the
      total number of votes it's received.

      Returns a dictionary with ``score`` and ``num_votes`` keys.

    * ``get_scores_in_bulk(objects)`` -- Gets score and vote count
      details for all the given objects. Score details consist of a
      dictionary which has ``score`` and ``num_vote`` keys.

      Returns a dictionary mapping object ids to score details.

    * ``get_top(Model, limit=10, reversed=False)`` -- Gets the top
      ``limit`` scored objects for a given model.

      If ``reversed`` is ``True``, the bottom ``limit`` scored objects
      are retrieved instead.

      Yields ``(object, score)`` tuples.

    * ``get_bottom(Model, limit=10)`` -- A convenience method which
      calls ``get_top`` with ``reversed=True``.

      Gets the bottom (i.e. most negative) ``limit`` scored objects
      for a given model.

      Yields ``(object, score)`` tuples.

    * ``get_for_user(obj, user)`` -- Gets the vote made on the given
      object by the given user, or ``None`` if no matching vote
      exists.

    * ``get_for_user_in_bulk(objects, user)`` -- Gets the votes
      made on all the given objects by the given user.

      Returns a dictionary mapping object ids to votes.

Basic usage
-----------

Recording votes and retrieving scores
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Votes are recorded using the ``record_vote`` helper function::

    >>> from django.contrib.auth.models import User
    >>> from shop.apps.products.models import Widget
    >>> from voting.models import Vote
    >>> user = User.objects.get(pk=1)
    >>> widget = Widget.objects.get(pk=1)
    >>> Vote.objects.record_vote(widget, user, +1)

The score for an object can be retrieved using the ``get_score``
helper function::

    >>> Vote.objects.get_score(widget)
    {'score': 1, 'num_votes': 1}

If the same user makes another vote on the same object, their vote
is either modified or deleted, as appropriate::

    >>> Vote.objects.record_vote(widget, user, -1)
    >>> Vote.objects.get_score(widget)
    {'score': -1, 'num_votes': 1}
    >>> Vote.objects.record_vote(widget, user, 0)
    >>> Vote.objects.get_score(widget)
    {'score': 0, 'num_votes': 0}


Generic Views
=============

The ``voting.views`` module contains two views:

* :py:class:`RecordVoteOnItemView` processes vote requests issued by users, redirecting to another URL on success
* :py:class:`ConfirmVoteOnItemView` just displays a confirmation page when a vote request has been successfully processed

The following sample URLconf demonstrates a basic usage of these generic views:

.. sourcecode:: python

    from django.conf.urls.defaults import *
    from voting.views import  RecordVoteOnItemView, ConfirmVoteOnItemView
    from shop.apps.products.models import Widget

    urlpatterns = patterns('',
        (r'^widgets/(?P<pk>\d+)/vote/(?P<direction>up|down|clear)/$',  RecordVoteOnItemView.as_view(model=Widget), 'widget_record_vote'),
        (r'^widgets/(?P<pk>\d+)/vote/confirm/(?P<direction>up|down|clear)/$', ConfirmVoteOnItemView.as_view(model=Widget), 'widget_confirm_vote'),
    )


.. py:class:: RecordVoteOnItemView

    Records the vote casted by the current (authenticated) user on a given model instance.
    
    Note that this is an abstract view, intended to be subclassed in order to make a given data model "votable". To do
    so, just set the ``model`` class attribute to the Django model's class whose instances have to be made votable.
    
    The model instance to be voted against is retrieved by the ``get_object()`` method.  The default implementation
    relies on the lookup logic provided by the built-in ``DetailView`` view.  In order for this lookup procedure to
    work, the view must receive either of these keyword arguments:

    * ``pk``: the value of the primary-key field for the object being voted on
    * ``slug``: the slug of the object being voted on

    If the ``slug`` parameter is used to identify the object, the view assumes that the corresponding model declares a
    ``SlugField`` named ``slug``.  If your model's slug field is named otherwise, be sure to set the ``slug_field``
    class attribute to the proper value.

    Moreover, the ``direction`` keyword argument must contain the kind of vote to be made (one of ``up``, ``down`` or
    ``clear``).
   
    After a (regular HTTP) vote request has been successfully processed, the view redirects the client to the URL
    returned by the ``get_success_url()`` method.  The default implementation of ``get_success_url()`` looks for the
    success URL in the following places, in order:
      
      * the ``post_vote_redirect`` class attribute, if set 
      * the ``next`` parameter of the incoming HTTP request, if any
      * the ``get_absolute_url()`` method of the object returned by the ``get_object()`` method
   
    If this strategy doesn't fit your needs, just override ``get_success_url()`` in concrete subclass.
    
    If instead the vote request is performed via AJAX, a JSON object is returned to the client by the
    ``get_json_response()`` method.  The default implementation build an object with the following properties:
    
    * ``success``: ``true`` if the vote was successfully registered, ``false`` otherwise
    * ``score``: an object having the properties ``score`` (the updated score for the given object) 
       and ``num_votes`` (the number of votes casted on the given object)
    * ``error_message``: a message describing an error condition occurred while processing the vote 

.. py:class:: ConfirmVoteOnItemView

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
    
    As usual, you can build a different context by providing a custom implementation of the 
    ``get_context_data()`` method.

Template tags
=============

The ``voting.templatetags.voting_tags`` module defines a number of
template tags which may be used to retrieve and display voting
details.

Tag reference
-------------

score_for_object
~~~~~~~~~~~~~~~~

Retrieves the total score for an object and the number of votes
it's received, storing them in a context variable which has ``score``
and ``num_votes`` properties.

Example usage::

    {% score_for_object widget as score %}

    {{ score.score }} point{{ score.score|pluralize }}
    after {{ score.num_votes }} vote{{ score.num_votes|pluralize }}

scores_for_objects
~~~~~~~~~~~~~~~~~~

Retrieves the total scores and number of votes cast for a list of
objects as a dictionary keyed with the objects' ids and stores it in a
context variable.

Example usage::

    {% scores_for_objects widget_list as scores %}

votes_for_object
~~~~~~~~~~~~~~~~

Retrieves the number of up-votes and down-votes for a given object and stores them in a context variable having ``upvotes`` and
``downvotes`` attributes.

Example usage::


   {% votes_for_object widget as widget_votes %}

   Widget {{ widget }} has been given {{ widget_votes.upvotes }} positive vote{{ widget_votes.upvotes|pluralize }} and 
   {{ widget_votes.downvotes }} negative vote{{ widget_votes.downvotes|pluralize }}.


vote_by_user
~~~~~~~~~~~~

Retrieves the ``Vote`` cast by a user on a particular object and
stores it in a context variable. If the user has not voted, the
context variable will be ``None``.

Example usage::

    {% vote_by_user user on widget as vote %}

votes_by_user
~~~~~~~~~~~~~

Retrieves the votes cast by a user on a list of objects as a
dictionary keyed with object ids and stores it in a context
variable.

Example usage::

    {% votes_by_user user on widget_list as vote_dict %}

dict_entry_for_item
~~~~~~~~~~~~~~~~~~~

Given an object and a dictionary keyed with object ids - as returned
by the ``votes_by_user`` and ``scores_for_objects`` template tags -
retrieves the value for the given object and stores it in a context
variable, storing ``None`` if no value exists for the given object.

Example usage::

    {% dict_entry_for_item widget from vote_dict as vote %}

confirm_vote_message
~~~~~~~~~~~~~~~~~~~~

Intended for use in vote confirmation templates, creates an appropriate
message asking the user to confirm the given vote for the given object
description.

Example usage::

    {% confirm_vote_message widget.title direction %}

Filter reference
----------------

vote_display
~~~~~~~~~~~~

Given a string mapping values for up and down votes, returns one
of the strings according to the given ``Vote``:

=========  =====================  =============
Vote type   Argument               Outputs
=========  =====================  =============
``+1``     ``'Bodacious,Bogus'``  ``Bodacious``
``-1``     ``'Bodacious,Bogus'``  ``Bogus``
=========  =====================  =============

If no string mapping is given, ``'Up'`` and ``'Down'`` will be used.

Example usage::

    {{ vote|vote_display:"Bodacious,Bogus" }}
