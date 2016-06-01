# -*- encoding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
#    Author: Goran Kliska
#    Copyright (C) 2011- 2013 Slobodni programi d.o.o., Zagreb
#                http://www.slobodni-programi.hr
#    Contributions:
#    Documentation: http://www.fina.hr/Default.aspx?sec=1266
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
# import logging


def mod11ini(value):
    '''
    Compute mod11ini
    '''
    length = len(value)
    s = 0
    for i in xrange(0, length):
        s += int(value[length - i - 1]) * (i + 2)
    res = s % 11
    if res > 1:
        res = 11 - res
    else:
        res = 0
    return str(res)


def iso7064(value):
    """
    Compute ISO 7064, Mod 11,10
    """
    t = 10
    for i in value:
        c = int(i)
        t = (2 * ((t + c) % 10 or 10)) % 11
    return str((11 - t) % 10)


def mod11p7(value):
    length = len(value)
    # ## if 1.st digit differs from three - ERROR
    # if not return_check_digit and int(value[0]) != 3:
    #    return False
    s = 0
    for i in xrange(0, length):
        s += int(value[length - i - 1]) * ((i % 6) + 2)
    res = s % 11
    if res == 0:
        return '5'
    elif res == 1:
        return '0'
    else:
        return str(11 - res)


def mod10zb(value):
    l = len(value)
    res = 0
    for i in xrange(0, l):
        res += int(value[l - i - 1]) * (i % 2 + 1)
    return str(res % 10)


def mod10(value):
    l = len(value)
    res = 0
    for i in xrange(0, l):
        num = int(value[l - i - 1]) * (((i + 1) % 2) + 1)
        res += (num / 10 + num % 10)
    res = res % 10
    if res == 0:
        return '0'
    else:
        return str(10 - res)


def mod11(value):
    l = len(value)
    res = 0
    for i in xrange(0, l):
        res += int(value[l - i - 1]) * (i % 6 + 2)
    res = res % 11
    if res > 1:
        return str(11 - res)
    else:
        return '0'


"""
# Test
mod11p7('3456789012') # res = '2'
mod10zb('223344556') #res='8'
mod7064('234000') #res='9'
mod11ini('33444555666') #res=9
mod10('54370395') #res=7
mod11('54370395') #res=8
"""


def reference_number_get(model='', P1='', P2='', P3='', P4=''):
    if not model:
        model = ''  # or '99'?
    if model == "HR01":
        res = '-'.join((P1, P2, P3 + mod11ini(P1 + P2 + P3)))
    elif model == "HR02":
        res = '-'.join((P1, P2 + mod11ini(P2), P3 + mod11ini(P3)))
    elif model == "HR03":
        res = '-'.join((P1 + mod11ini(P1), P2 + mod11ini(P2), P3 + mod11ini(P3)))
    elif model == "HR04":
        res = '-'.join((P1 + mod11ini(P1), P2, P3 + mod11ini(P3)))
    elif model == "HR05":
        res = '-'.join((P1 + mod11ini(P1), P2, P3))
    elif model == "HR06":
        res = '-'.join((P1, P2, P3 + mod11ini(P2 + P3)))
    elif model == "HR07":
        res = '-'.join((P1, P2 + mod11ini(P2), P3))
    elif model == "HR08":
        res = '-'.join((P1, P2 + mod11ini(P1 + P2), P3 + mod11ini(P3)))
    elif model == "HR09":
        res = '-'.join((P1, P2 + mod11ini(P1 + P2), P3))
    elif model == "HR10":
        res = '-'.join((P1 + mod11ini(P1), P2, P3 + mod11ini(P2 + P3)))
    elif model == "HR11":
        res = '-'.join((P1 + mod11ini(P1), P2 + mod11ini(P2), P3))
    elif model == "HR13":
        res = '-'.join((P1 + mod11p7(P1), P2, P3))
    elif model == "HR14":
        res = '-'.join((P1 + mod10zb(P1), P2, P3))
    elif model == "HR15":
        res = '-'.join((P1 + mod10(P1), P2 + mod10(P2)))
    elif model == "HR16":
        res = '-'.join((P1 + mod11ini(P1), P2 + mod11ini(P2), P3))
    elif model == "HR17":
        res = '-'.join((P1 + iso7064(P1), P2, P3))
    elif model == "HR18":
        res = '-'.join((P1 + mod11p7(P1), P2, P3))
    elif model == "HR21":
        res = '-'.join((P1 + mod11ini(P1), P2 + mod11ini(P2), P3))
    elif model == "HR23":
        res = '-'.join((P1 + mod11ini(P1), P2, P3, P4))
    elif model == "HR24":
        res = '-'.join((P1 + mod11ini(P1), P2, P3, P4))
    elif model == "HR26":
        res = '-'.join((P1 + mod11ini(P1), P2 + mod11ini(P2), P3 + mod11ini(P3), P4))
    elif model == "HR27":
        res = '-'.join((P1 + mod11ini(P1), P2 + mod11ini(P2)))
    elif model == "HR28":
        res = '-'.join((P1 + mod11ini(P1), P2 + mod11ini(P2), P3 + mod11ini(P3), P4))
    elif model == "HR29":
        res = '-'.join((P1 + mod11ini(P1), P2 + mod11ini(P2), P3 + mod11ini(P3)))
    elif model == "HR31":
        res = '-'.join((P1 + iso7064(P1), P2, P3, P4))
    elif model == "HR33":
        res = '-'.join((P1 + iso7064(P1), P2 + iso7064(P2), P3))
    elif model == "HR34":
        res = '-'.join((P1 + iso7064(P1), P2 + iso7064(P2), P3 + iso7064(P3)))
    elif model == "HR40":
        res = '-'.join((P1 + mod10(P1), P2, P3))
    elif model == "HR43":
        res = '-'.join((P1, P2 + mod11ini(P2), P3, P4))
    elif model == "HR55":
        res = '-'.join((P1 + mod11ini(P1), P2, P3))
    elif model == "HR62":
        res = '-'.join((P1 + mod11ini(P1), P2 + iso7064(P2), P3 + mod11ini(P3), P4))
    elif model == "HR63":
        res = '-'.join((P1 + mod11ini(P1), P2 + iso7064(P2), P3 + mod11ini(P3)))
    elif model == "HR64":
        res = '-'.join((P1 + mod11ini(P1), P2 + iso7064(P2), P3, P4))
    elif model == "HR65":
        res = '-'.join((P1 + mod11ini(P1), P2 + mod11ini(P2), P3 + iso7064(P3), P4))
    elif model == "HR66":
        res = '-'.join((P1, P2[:7] + mod11ini(P2[:7]) + P2[7:], P3))
    elif model == "HR83":
        res = '-'.join(((P1 + mod11ini(P1), P2, P3)))
    elif model == "HR84":
        if len(P2) == 4:
            res = '-'.join((P1 + mod11ini(P1), P2, P3))
        else:
            res = '-'.join(((P1 + mod11ini(P1), P2)))
    else:  # model in ('','00',"99")
        res = (P1 + '-' + P2 + '-' + P3 + '-' + P4)

    res.strip('-')
    res = res.strip('-').replace('---', '-').replace('--', '-')

    return res


# 1.   = V-variable,mandatory
#      = v-variable,optional
#      = F-fixed lenght,mandatory
#      = f-fixed lenght,optional
# 2-3. =max lenght
# 4.   = K - control num
#      = k - control num if right one does not exists ???
#      = n - NO control num
MODELS_LENGTH = {
    "01": ('V12k', 'v12k', 'v12K', 'n00n'),
    "02": ('V12n', 'v12K', 'v12K', 'n00n'),
    "03": ('V12K', 'v12K', 'v12K', 'n00n'),

    "12": ('F13K', 'v12n', 'v12n', 'n00n'),
}


# TODO
def validate_lengths(model, value):
    return True


# TODO
def reference_number_valid(model='', P=''):
    return True
