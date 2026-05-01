import ipaddress
import socket
from urllib.parse import urlparse

import requests

from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect, get_object_or_404

from .forms import RegisterForm, NoteForm
from .models import Note


def home(request):
    return render(request, "notes/home.html")


def register_view(request):
    error = None

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            # flaw 4: identification and authentication Failure
            # weak passwords are accepted without validation
            user = User.objects.create_user(username=username, password=password)

            # fix:
            # try:
            #     validate_password(password)
            #     user = User.objects.create_user(username=username, password=password)
            # except ValidationError as e:
            #     error = " ".join(e.messages)
            #     return render(request, "notes/register.html", {"form": form, "error": error})

            login(request, user)
            return redirect("notes")
    else:
        form = RegisterForm()

    return render(request, "notes/register.html", {"form": form, "error": error})


def login_view(request):
    error = None

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        # flaw 4: identification and authentication Failure
        # different errors reveal whether a username exists.
        if not User.objects.filter(username=username).exists():
            error = "No such username exists."
        else:
            user = authenticate(request, username=username, password=password)
            if user is None:
                error = "Wrong password."
            else:
                login(request, user)
                return redirect("notes")

        # fix:
        # user = authenticate(request, username=username, password=password)
        # if user is None:
        #     error = "Invalid username or password."
        # else:
        #     login(request, user)
        #     return redirect("notes")

    return render(request, "notes/login.html", {"error": error})


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def notes_view(request):
    notes = Note.objects.filter(owner=request.user).order_by("-created_at")
    return render(request, "notes/notes.html", {"notes": notes})


@login_required
def note_create_view(request):
    if request.method == "POST":
        form = NoteForm(request.POST)

        if form.is_valid():
            note = form.save(commit=False)
            note.owner = request.user

            # flaw 2: Cryptographic Failure
            # sensitive secret_value is stored in plaintext.
            note.save()

            # fix:
            # from django.contrib.auth.hashers import make_password
            # note.secret_value = make_password(note.secret_value)
            # note.save()

            return redirect("notes")
    else:
        form = NoteForm()

    return render(request, "notes/note_form.html", {"form": form, "mode": "Create"})


@login_required
def note_detail_view(request, note_id):
    # flaw 1: broken access control
    # any logged-in user can view another user's note by changing the ID.
    note = get_object_or_404(Note, id=note_id)

    # fix:
    # note = get_object_or_404(Note, id=note_id, owner=request.user)

    return render(request, "notes/note_detail.html", {"note": note})


@login_required
def note_edit_view(request, note_id):
    # flaw 1: broken access control
    # any logged-in user can edit another user's note by changing the ID.
    note = get_object_or_404(Note, id=note_id)

    # fix:
    # note = get_object_or_404(Note, id=note_id, owner=request.user)

    if request.method == "POST":
        form = NoteForm(request.POST, instance=note)

        if form.is_valid():
            form.save()
            return redirect("note_detail", note_id=note.id) # type: ignore
    else:
        form = NoteForm(instance=note)

    return render(request, "notes/note_form.html", {"form": form, "mode": "Edit"})


@login_required
def search_view(request):
    q = request.GET.get("q", "")
    notes = []

    if q:
        # flaw 3: injection
        # user input is directly inserted into raw SQL.
        
        sql = f"""
            SELECT id, owner_id, title, content, secret_value, created_at
            FROM notes_note
            WHERE title LIKE '%{q}%'
        """
        notes = list(Note.objects.raw(sql))

        # fix:
        # notes = list(Note.objects.raw(
        #     """
        #     SELECT id, owner_id, title, content, secret_value, created_at
        #     FROM notes_note
        #     WHERE owner_id = %s AND title LIKE %s
        #     """,
        #     [request.user.id, f"%{q}%"]
        # ))

    return render(request, "notes/search.html", {"q": q, "notes": notes})


@login_required
def fetch_url_view(request):
    result = None
    error = None

    if request.method == "POST":
        url = request.POST.get("url", "")

        try:
            # flaw 5: server-side request forgery
            # the backend fetches any URL given by the user.
            response = requests.get(url, timeout=3)
            result = response.text[:1000]

            # fix:
            # parsed = urlparse(url)
            # if parsed.scheme not in ["http", "https"]:
            #     raise ValueError("Only HTTP and HTTPS URLs are allowed.")
            #
            # hostname = parsed.hostname
            # ip = ipaddress.ip_address(socket.gethostbyname(hostname))
            #
            # if ip.is_private or ip.is_loopback or ip.is_link_local:
            #     raise ValueError("Private, local, and internal addresses are blocked.")
            #
            # response = requests.get(url, timeout=3)
            # result = response.text[:1000]

        except Exception as e:
            error = str(e)

    return render(request, "notes/fetch_url.html", {"result": result, "error": error})