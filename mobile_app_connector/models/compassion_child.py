# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import models, api
from ..mappings.compassion_child_mapping import MobileChildMapping

logger = logging.getLogger(__name__)


class CompassionChild(models.Model):
    """ A sponsored child """
    _inherit = 'compassion.child'

    def get_app_json_no_wrap(self):
        """
        Called by HUB when data is needed for a tiles letters
        :return: dictionary with JSON data of the child
        """
        if not self:
            return {}
        mapping = MobileChildMapping(self.env)
        if len(self) == 1:
            data = mapping.get_connect_data(self)
        else:
            data = []
            for child in self:
                data.append(mapping.get_connect_data(child))
        return data

    @api.multi
    def get_app_json(self, multi=False):
        """
        Called by HUB when data is needed for a tile
        :param multi: used to change the wrapper if needed
        :return: dictionary with JSON data of the children
        """
        children_pictures = self.sudo().mapped('pictures_ids')
        project = self.sudo().mapped('project_id')

        if not self:
            return {}
        mapping = MobileChildMapping(self.env)
        wrapper = 'Children' if multi else 'Child'
        if len(self) == 1 and not multi:
            data = mapping.get_connect_data(self)
        else:
            data = []
            for child in self:
                data.append(mapping.get_connect_data(child))
        return {
            wrapper: data,
            'Images': children_pictures.filtered(
                lambda r: r.image_url).get_app_json(multi=True),
            'Location':
                project.get_location_json(multi=False),
            'Time': {
                    "ChildTime": project.get_time()[0],
                    "ChildTimezone": project[0].timezone,
                    },
            'OrderDate': max(x for y in self
                             for x in y.sponsorship_ids.mapped('start_date')),
            'Weather': project[0].get_weather_json(multi=False)

        }

    @api.model
    def mobile_sponsor_children(self, **other_params):
        """
        Mobile app method:
        Returns the sponsored child list for a given sponsor.
        :param userid: the ref of the sponsor
        :param other_params: all request parameters
        :return: JSON list of sponsor children data
        """
        result = []
        partner_ref = self._get_required_param('userid', other_params)

        sponsor = self.env['res.partner'].search([
            # TODO change filter, we can directly search for connected user
            ('ref', '=', partner_ref),
        ], limit=1)
        children = self.search([
            ('partner_id', '=', sponsor.id)
        ])

        mapping = MobileChildMapping(self.env)
        for child in children:
            result.append(mapping.get_connect_data(child))
        return result

    @api.model
    def mobile_get_child_bio(self, **other_params):
        """
        Mobile app method:
        Returns child bio of a given child
        :param other_params: child's global id
        :return: JSON list of child bio information
        """
        child = self.env['compassion.child'].search([
            ('global_id', '=', str(other_params['globalId']))
        ])

        household = child.household_id

        guardians = household.member_ids.filtered(lambda x: x['is_caregiver'])\
            .translate('role')

        at = self.env['ir.advanced.translation'].sudo()
        childBio = {
            'educationLevel': child.translate('education_level').lower(),
            'academicPerformance': child.translate(
                'academic_performance').lower(),
            'maleGuardianJob': at.get(
                household.translate('male_guardian_job')),
            'femaleGuardianJob': at.get(
                household.translate('female_guardian_job'), female=True),
            'maleGuardianJobType': household.translate(
                'male_guardian_job_type'),
            'femaleGuardianJobType': household.translate(
                'female_guardian_job_type'),
            'hobbies': child.translate('hobby_ids.value'),
            'guardians': guardians,
            'notEnrolledReason': (child.not_enrolled_reason or '').lower()
        }

        result = {
            'ChildBioServiceResult': childBio
        }
        return result

    def _get_required_param(self, key, params):
        if key not in params:
            raise ValueError('Required parameter {}'.format(key))
        return params[key]
