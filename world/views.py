import json

from django.shortcuts import render
from django.contrib.auth import login, logout
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from django.db import IntegrityError

from haystack.query import SearchQuerySet

from .util import otp_generator, send_otp_email, validate_otp
from .models import User,Team, Player,Match,Standing

@login_required
def home(request):
    return render(request, "home.html")

@login_required
def search(request):
    query = request.GET.get("query", "").strip()
    result = {"cities": [], "countries": [], "languages": []}
    
    if not query and len(query) < 3:
        return JsonResponse(result)

    team_pks = list(SearchQuerySet().autocomplete(i_city_name=query).values_list("pk", flat=True))
    player_pks = list(SearchQuerySet().autocomplete(i_country_name=query).values_list("pk", flat=True))

    result["teams"] = [ Team.objects.filter(pk=team_pk).values().first() for team_pk in team_pks ]
    result["players"] = [ Player.objects.filter(pk=player_pk).values().first() for player_pk in player_pks ]

    return render(request, "search_results.html", result)

def signup(request):
    return render(request, "signup.html")

@csrf_exempt
def signup_validate(request):
    body = json.loads(request.body)
    email = body.get("email", "")
    first_name = body.get("first_name", "")
    last_name = body.get("last_name", "")
    gender = body.get("gender", "female")
    phone_number = body.get("phone_number", "")

    if not email:
        result = {"success": False, "message": "email not found"}
        return JsonResponse(result)

    if not first_name:
        result = {"success": False, "message": "first name not found"}
        return JsonResponse(result)

    try:
        User.objects.create(email=email, 
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            gender=gender
        )
    except IntegrityError:
        result = {"success": False, "message": "user already exists"}
        return JsonResponse(result)

    otp = otp_generator()
    otp_status = send_otp_email(email, otp)
    
    if not otp_status:
        result = {"success": False, "message": "incorrect email"}
        return JsonResponse(result)
 
    request.session["auth_otp"] = otp
    request.session["auth_email"] = email
    # cache.set('{0}_auth_otp'.format(request.session.session_key), otp, 120)
    # cache.set('{0}_auth_email'.format(request.session.session_key), email, 120)
    result = {"success": True, "message": "otp sent to email"}
    return JsonResponse(result)

def c_login(request):
    return render(request, "login.html")


@csrf_exempt
def send_otp(request):
    '''
    When you will click on 'Send Otp" button on front end then ajax call will be hit and
    that lead to call this function
    '''
    body = json.loads(request.body)
    email = body.get("email", "")

    otp = otp_generator()
    otp_status = send_otp_email(email, otp)
    if not otp_status:
        result = {"success": False, "message": "incorrect email"}
        return JsonResponse(result)
    
    request.session["auth_otp"] = otp
    request.session["auth_email"] = email
    # cache.set('{0}_auth_otp'.format(request.session.session_key), otp, 120)
    # cache.set('{0}_auth_email'.format(request.session.session_key), email, 120)
 
    result = {"successs": True, "message": "otp sent"}
    return JsonResponse(result)

@csrf_exempt
# def login_validate(request):
#     body = json.loads(request.body)
#     sent_otp = request.session.get("auth_otp", "")
#     sent_email = request.session.get("auth_email", "")
#     email = body.get("email", "")
#     otp = body.get("otp", "")
#
#     result = validate_otp(otp, sent_otp, email, sent_email)
#
#     if not result["success"]:
#         return JsonResponse(result)
#
#     try:
#         user = User.objects.get(email=email)
#     except ObjectDoesNotExist:
#         result = {"success": False, "message": "please signup"}
#         return JsonResponse(result)
#
#     login(request, user)
#     result = {"success": True, "message": "login succeeded"}
#     return JsonResponse(result)

# 直接登录
def login_validate(request):
    body = json.loads(request.body)
    email = body.get("email", "")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # 如果用户不存在，直接返回一个错误信息
        return JsonResponse({"success": False, "message": "User does not exist. Please sign up."})

    # 如果用户存在，直接登录该用户
    login(request, user)
    return JsonResponse({"success": True, "message": "Logged in successfully"})

@login_required
def c_logout(request):
    logout(request)
    return HttpResponseRedirect("/login")



def get_standing(request):
    # 这里假设你有一个模型名为Team，包含队伍的信息
    standing = Standing.objects.all().order_by('rank')

    return render(request, 'standing.html', {'Standing': standing})

def get_team_details(request, teamid):
    # 根据 teamid 获取球队详情
    team_detail = Team.objects.filter(teamid=teamid)

    # 根据 teamid 获取该队的已结束比赛数据
    matches = Match.objects.filter(status='已结束', hostteamid=teamid) \
              | Match.objects.filter(status='已结束',  guestteamid=teamid).order_by('date')[:10]

    # 根据 teamid 获取该队的所有球员数据
    players = Player.objects.filter(teamid=teamid)

    context = {
        'team_detail': team_detail,
        'matches': matches,
        'players': players,
    }
    return render(request, 'team_detail.html', context)

def get_match_details (request,matchid):
    match_detail = Match.objects.filter(matchid=matchid)
    players = Player.objects.filter(matchid=matchid)
    context = {
        'match_details': match_detail,
        'players': players,
    }
    return render(request, 'match.html', context)