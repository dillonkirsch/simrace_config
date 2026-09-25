"""Canonical control names across supported simulators.

This module is a read-only vocabulary crosswalk.  It deliberately does not
enable writing bindings: an adapter still has to prove the native file format,
device identity, and button/axis encoding before it may apply a mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ControlKind = Literal["axis", "axis_or_button", "button", "gear"]
MappingStatus = Literal[
    "exact", "compound", "related", "not_exposed", "not_observed"
]


@dataclass(frozen=True, slots=True)
class ControlName:
    """App-owned, simulator-independent name shown to a driver."""

    label: str
    kind: ControlKind


@dataclass(frozen=True, slots=True)
class NativeControlName:
    """One simulator's representation of a canonical control.

    ``compound`` means the listed native name contains multiple directions or
    actions and needs more format research before it can be written safely.
    ``related`` identifies a native action with narrower or different
    semantics that must not be silently treated as equivalent. ``not_exposed``
    is evidence that the installed action vocabulary has no such control.
    ``not_observed`` is weaker: no identifier was found in the inspected local
    data, so absence must not be treated as unsupported.
    """

    names: tuple[str, ...] = ()
    status: MappingStatus = "exact"
    note: str = ""


GAMES = {
    "iracing": "iRacing",
    "assetto_corsa": "Assetto Corsa",
    "assetto_corsa_competizione": "Assetto Corsa Competizione",
    "assetto_corsa_evo": "Assetto Corsa EVO",
    "automobilista_2": "Automobilista 2",
    "le_mans_ultimate": "Le Mans Ultimate",
}


BASIC_CONTROLS: dict[str, ControlName] = {
    "steering": ControlName("Steering", "axis"),
    "accelerator": ControlName("Accelerator (throttle)", "axis"),
    "brake": ControlName("Brake pedal", "axis"),
    "clutch": ControlName("Clutch pedal", "axis"),
    "shift_up": ControlName("Shift up", "button"),
    "shift_down": ControlName("Shift down", "button"),
    "reverse_gear": ControlName("Reverse gear", "gear"),
    "neutral_gear": ControlName("Neutral gear", "gear"),
    **{
        f"gear_{number}": ControlName(f"Gear {number}", "gear")
        for number in range(1, 10)
    },
    "handbrake": ControlName("Handbrake", "axis_or_button"),
    "ignition": ControlName("Ignition", "button"),
    "starter": ControlName("Engine starter", "button"),
    "pit_limiter": ControlName("Pit speed limiter", "button"),
}


COMMON_CONTROLS: dict[str, ControlName] = {
    "headlights": ControlName("Cycle headlights", "button"),
    "headlights_flash": ControlName("Flash headlights", "button"),
    "wipers": ControlName("Cycle wipers", "button"),
    "horn": ControlName("Horn", "button"),
    "look_left": ControlName("Look left", "button"),
    "look_right": ControlName("Look right", "button"),
    "look_rear": ControlName("Look behind", "button"),
    "next_camera": ControlName("Next driving camera", "button"),
    "brake_bias_increase": ControlName("Move brake bias forward", "button"),
    "brake_bias_decrease": ControlName("Move brake bias rearward", "button"),
    "tc_increase": ControlName("Increase traction control", "button"),
    "tc_decrease": ControlName("Decrease traction control", "button"),
    "tc_toggle": ControlName("Toggle traction control", "button"),
    "abs_increase": ControlName("Increase ABS", "button"),
    "abs_decrease": ControlName("Decrease ABS", "button"),
    "abs_toggle": ControlName("Toggle ABS", "button"),
    "drs": ControlName("DRS", "button"),
    "overtake": ControlName("Overtake / push-to-pass", "button"),
    "reset_car": ControlName("Reset car", "button"),
    "pause": ControlName("Pause", "button"),
}


ADVANCED_CONTROLS: dict[str, ControlName] = {
    "fuel_mixture_increase": ControlName("Increase fuel mixture", "button"),
    "fuel_mixture_decrease": ControlName("Decrease fuel mixture", "button"),
    "engine_map_increase": ControlName("Increase engine map", "button"),
    "engine_map_decrease": ControlName("Decrease engine map", "button"),
    "engine_braking_increase": ControlName("Increase engine braking", "button"),
    "engine_braking_decrease": ControlName("Decrease engine braking", "button"),
    "turbo_boost_increase": ControlName("Increase turbo boost", "button"),
    "turbo_boost_decrease": ControlName("Decrease turbo boost", "button"),
    "front_arb_increase": ControlName("Stiffen front anti-roll bar", "button"),
    "front_arb_decrease": ControlName("Soften front anti-roll bar", "button"),
    "rear_arb_increase": ControlName("Stiffen rear anti-roll bar", "button"),
    "rear_arb_decrease": ControlName("Soften rear anti-roll bar", "button"),
    "weight_jacker_increase": ControlName("Increase weight jacker", "button"),
    "weight_jacker_decrease": ControlName("Decrease weight jacker", "button"),
    "ers_deployment_increase": ControlName("Increase ERS deployment", "button"),
    "ers_deployment_decrease": ControlName("Decrease ERS deployment", "button"),
    "ers_regen_increase": ControlName("Increase ERS regeneration", "button"),
    "ers_regen_decrease": ControlName("Decrease ERS regeneration", "button"),
    "launch_control": ControlName("Launch control", "button"),
    "rain_light": ControlName("Rain light", "button"),
    "indicator_left": ControlName("Left turn signal", "button"),
    "indicator_right": ControlName("Right turn signal", "button"),
    "hazard_lights": ControlName("Hazard lights", "button"),
    "mfd_next": ControlName("Next MFD", "button"),
    "mfd_previous": ControlName("Previous MFD", "button"),
    "hud_toggle": ControlName("Toggle HUD", "button"),
    "dash_page_next": ControlName("Next dashboard page", "button"),
    "dash_page_previous": ControlName("Previous dashboard page", "button"),
    "pit_request": ControlName("Request pit stop", "button"),
    "pit_menu_up": ControlName("Pit menu up", "button"),
    "pit_menu_down": ControlName("Pit menu down", "button"),
    "pit_menu_increase": ControlName("Increase pit-menu value", "button"),
    "pit_menu_decrease": ControlName("Decrease pit-menu value", "button"),
    "driving_aids": ControlName("Cycle driving aids", "button"),
    "ffb_gain_increase": ControlName("Increase force-feedback gain", "button"),
    "ffb_gain_decrease": ControlName("Decrease force-feedback gain", "button"),
    "seat_up": ControlName("Move seat up", "button"),
    "seat_down": ControlName("Move seat down", "button"),
    "seat_forward": ControlName("Move seat forward", "button"),
    "seat_backward": ControlName("Move seat backward", "button"),
    "fov_increase": ControlName("Increase field of view", "button"),
    "fov_decrease": ControlName("Decrease field of view", "button"),
    "virtual_mirror_toggle": ControlName("Toggle virtual mirror", "button"),
    "driver_labels_toggle": ControlName("Toggle driver labels", "button"),
    "push_to_talk": ControlName("Push to talk", "button"),
    "screenshot": ControlName("Take screenshot", "button"),
    "recenter_vr": ControlName("Recenter VR view", "button"),
    "tearoff_visor": ControlName("Tear off visor", "button"),
    "rev_limiter": ControlName("Rev limiter", "button"),
    "hud_cycle": ControlName("Cycle HUD mode", "button"),
}


TUNING_CONTROLS: dict[str, ControlName] = {
    "brake_bias_fine_increase": ControlName("Move brake bias slightly forward", "button"),
    "brake_bias_fine_decrease": ControlName("Move brake bias slightly rearward", "button"),
    "peak_brake_bias_increase": ControlName("Increase peak brake bias", "button"),
    "peak_brake_bias_decrease": ControlName("Decrease peak brake bias", "button"),
    "brake_migration_forward": ControlName("Move brake migration forward", "button"),
    "brake_migration_rearward": ControlName("Move brake migration rearward", "button"),
    "tc_2_increase": ControlName("Increase traction control 2", "button"),
    "tc_2_decrease": ControlName("Decrease traction control 2", "button"),
    "tc_slip_angle_increase": ControlName("Increase TC slip-angle target", "button"),
    "tc_slip_angle_decrease": ControlName("Decrease TC slip-angle target", "button"),
    "tc_cut_increase": ControlName("Increase traction-control cut", "button"),
    "tc_cut_decrease": ControlName("Decrease traction-control cut", "button"),
    "tc_override": ControlName("Traction-control override", "button"),
    "diff_preload_increase": ControlName("Increase differential preload", "button"),
    "diff_preload_decrease": ControlName("Decrease differential preload", "button"),
    "diff_entry_increase": ControlName("Increase differential entry setting", "button"),
    "diff_entry_decrease": ControlName("Decrease differential entry setting", "button"),
    "diff_middle_increase": ControlName("Increase differential mid-corner setting", "button"),
    "diff_middle_decrease": ControlName("Decrease differential mid-corner setting", "button"),
    "diff_exit_increase": ControlName("Increase differential exit setting", "button"),
    "diff_exit_decrease": ControlName("Decrease differential exit setting", "button"),
    "diff_power_increase": ControlName("Increase differential power setting", "button"),
    "diff_power_decrease": ControlName("Decrease differential power setting", "button"),
    "diff_coast_increase": ControlName("Increase differential coast setting", "button"),
    "diff_coast_decrease": ControlName("Decrease differential coast setting", "button"),
    "front_wing_increase": ControlName("Increase front wing or flap", "button"),
    "front_wing_decrease": ControlName("Decrease front wing or flap", "button"),
    "rear_wing_increase": ControlName("Increase rear wing or flap", "button"),
    "rear_wing_decrease": ControlName("Decrease rear wing or flap", "button"),
    "power_steering_increase": ControlName("Increase power steering", "button"),
    "power_steering_decrease": ControlName("Decrease power steering", "button"),
    "throttle_shape_increase": ControlName("Increase throttle shaping", "button"),
    "throttle_shape_decrease": ControlName("Decrease throttle shaping", "button"),
    "engine_power_increase": ControlName("Increase engine power setting", "button"),
    "engine_power_decrease": ControlName("Decrease engine power setting", "button"),
    "fuel_cut_increase": ControlName("Increase fuel-cut position", "button"),
    "fuel_cut_decrease": ControlName("Decrease fuel-cut position", "button"),
    "launch_rpm_increase": ControlName("Increase launch RPM", "button"),
    "launch_rpm_decrease": ControlName("Decrease launch RPM", "button"),
    "track_bar_increase": ControlName("Raise track bar", "button"),
    "track_bar_decrease": ControlName("Lower track bar", "button"),
    "single_wipe": ControlName("Single windshield wipe", "button"),
    "low_fuel_acknowledge": ControlName("Acknowledge low-fuel warning", "button"),
    "in_lap_toggle": ControlName("Toggle in-lap mode", "button"),
    "full_course_yellow": ControlName("Toggle full-course yellow mode", "button"),
    "fuel_to_end_toggle": ControlName("Toggle fuel-to-end display", "button"),
    "fuel_to_end_margin_increase": ControlName("Increase fuel-to-end margin", "button"),
    "fuel_to_end_margin_decrease": ControlName("Decrease fuel-to-end margin", "button"),
    "skip_formation": ControlName("Skip formation sequence", "button"),
    "ai_control_toggle": ControlName("Toggle AI control", "button"),
}


SYSTEM_CONTROLS: dict[str, ControlName] = {
    "brake_misc_increase": ControlName("Increase miscellaneous brake setting", "button"),
    "brake_misc_decrease": ControlName("Decrease miscellaneous brake setting", "button"),
    "tc_3_increase": ControlName("Increase traction control 3", "button"),
    "tc_3_decrease": ControlName("Decrease traction control 3", "button"),
    "tc_4_increase": ControlName("Increase traction control 4", "button"),
    "tc_4_decrease": ControlName("Decrease traction control 4", "button"),
    "shock_left_front_increase": ControlName("Increase left-front shock setting", "button"),
    "shock_left_front_decrease": ControlName("Decrease left-front shock setting", "button"),
    "shock_right_front_increase": ControlName("Increase right-front shock setting", "button"),
    "shock_right_front_decrease": ControlName("Decrease right-front shock setting", "button"),
    "shock_left_rear_increase": ControlName("Increase left-rear shock setting", "button"),
    "shock_left_rear_decrease": ControlName("Decrease left-rear shock setting", "button"),
    "shock_right_rear_increase": ControlName("Increase right-rear shock setting", "button"),
    "shock_right_rear_decrease": ControlName("Decrease right-rear shock setting", "button"),
    "front_bump_damper_increase": ControlName("Increase front bump damping", "button"),
    "front_bump_damper_decrease": ControlName("Decrease front bump damping", "button"),
    "front_rebound_damper_increase": ControlName("Increase front rebound damping", "button"),
    "front_rebound_damper_decrease": ControlName("Decrease front rebound damping", "button"),
    "rear_bump_damper_increase": ControlName("Increase rear bump damping", "button"),
    "rear_bump_damper_decrease": ControlName("Decrease rear bump damping", "button"),
    "rear_rebound_damper_increase": ControlName("Increase rear rebound damping", "button"),
    "rear_rebound_damper_decrease": ControlName("Decrease rear rebound damping", "button"),
    "active_suspension_damping_increase": ControlName("Increase active-suspension damping", "button"),
    "active_suspension_damping_decrease": ControlName("Decrease active-suspension damping", "button"),
    "active_suspension_reaction_increase": ControlName("Increase suspension reaction speed", "button"),
    "active_suspension_reaction_decrease": ControlName("Decrease suspension reaction speed", "button"),
    "mguk_fixed_deployment_increase": ControlName("Increase fixed MGU-K deployment", "button"),
    "mguk_fixed_deployment_decrease": ControlName("Decrease fixed MGU-K deployment", "button"),
    "ers_heat_charging_toggle": ControlName("Toggle ERS heat charging", "button"),
    "rf_brake_attachment_toggle": ControlName("Toggle right-front brake attachment", "button"),
    "fuel_no_cut_toggle": ControlName("Toggle fuel no-cut mode", "button"),
    "hybrid_boost_hold": ControlName("Hold hybrid boost", "button"),
    "hybrid_regen_hold": ControlName("Hold hybrid regeneration", "button"),
    "hybrid_no_boost_toggle": ControlName("Toggle hybrid no-boost mode", "button"),
    "seat_angle_up": ControlName("Tilt seat up", "button"),
    "seat_angle_down": ControlName("Tilt seat down", "button"),
    "seat_reset": ControlName("Reset seat position", "button"),
    "track_map_cycle": ControlName("Cycle track map", "button"),
    "map_open": ControlName("Open map", "button"),
    "vehicle_status": ControlName("Show vehicle status", "button"),
    "driver_list": ControlName("Show driver list", "button"),
    "lap_info_cycle": ControlName("Cycle lap information", "button"),
    "radio_station_next": ControlName("Next radio station", "button"),
    "text_chat": ControlName("Open text chat", "button"),
    "voice_channel_next": ControlName("Next voice-chat channel", "button"),
    "voice_channel_previous": ControlName("Previous voice-chat channel", "button"),
    "voice_mute": ControlName("Mute voice chat", "button"),
    "spotter_mute": ControlName("Mute spotter", "button"),
    "ffb_reset": ControlName("Reset force feedback", "button"),
    "ffb_auto_adjust": ControlName("Automatically adjust force feedback", "button"),
}


UTILITY_CONTROLS: dict[str, ControlName] = {
    **{
        f"gear_{number}": ControlName(f"Gear {number}", "gear")
        for number in range(10, 17)
    },
    "ui_up": ControlName("Menu up", "button"),
    "ui_down": ControlName("Menu down", "button"),
    "ui_left": ControlName("Menu left", "button"),
    "ui_right": ControlName("Menu right", "button"),
    "ui_confirm": ControlName("Menu confirm", "button"),
    "ui_cancel": ControlName("Menu cancel", "button"),
    "ui_menu": ControlName("Open menu", "button"),
    "ui_page_up": ControlName("Menu page up", "button"),
    "ui_page_down": ControlName("Menu page down", "button"),
    "mirrors_cycle": ControlName("Cycle mirrors", "button"),
    "mirror_pitch_up": ControlName("Tilt mirror up", "button"),
    "mirror_pitch_down": ControlName("Tilt mirror down", "button"),
    "mirror_yaw_left": ControlName("Turn mirror left", "button"),
    "mirror_yaw_right": ControlName("Turn mirror right", "button"),
    "mirror_fov_increase": ControlName("Increase mirror field of view", "button"),
    "mirror_fov_decrease": ControlName("Decrease mirror field of view", "button"),
    "h_shifter_toggle": ControlName("Toggle H-pattern shifter", "button"),
    "stability_control_toggle": ControlName("Toggle stability control", "button"),
    "auto_clutch_toggle": ControlName("Toggle automatic clutch", "button"),
    "auto_gears_toggle": ControlName("Toggle automatic gears", "button"),
    "auto_brake_toggle": ControlName("Toggle automatic braking", "button"),
    "auto_steer_toggle": ControlName("Toggle automatic steering", "button"),
    "tc_force_on": ControlName("Force traction control on", "button"),
    "tc_force_off": ControlName("Force traction control off", "button"),
    "retractable_headlights_toggle": ControlName("Toggle retractable headlights", "button"),
    "esc_increase": ControlName("Increase stability-control level", "button"),
    "esc_decrease": ControlName("Decrease stability-control level", "button"),
    "mguh_mode": ControlName("Cycle MGU-H mode", "button"),
    "nitrous": ControlName("Nitrous", "button"),
    "telltale_reset": ControlName("Reset dashboard telltales", "button"),
    "hand_warning": ControlName("Raise driver hand warning", "button"),
    "dash_page_2_next": ControlName("Next secondary dashboard page", "button"),
    "dash_page_2_previous": ControlName("Previous secondary dashboard page", "button"),
    "pit_summary_toggle": ControlName("Toggle pit summary", "button"),
    "driving_line_toggle": ControlName("Toggle driving line", "button"),
    "speed_gear_display_toggle": ControlName("Toggle speed and gear display", "button"),
    "radio_display_toggle": ControlName("Toggle radio display", "button"),
    "ui_scale_increase": ControlName("Increase interface scale", "button"),
    "ui_scale_decrease": ControlName("Decrease interface scale", "button"),
    "show_points_of_interest": ControlName("Show points of interest", "button"),
    "cursor_toggle": ControlName("Toggle cursor", "button"),
    "look_up": ControlName("Look up", "button"),
    "look_down": ControlName("Look down", "button"),
    **{
        f"quick_chat_{number}": ControlName(f"Quick chat {number}", "button")
        for number in range(1, 16)
    },
    "voice_driver_mute": ControlName("Mute selected driver", "button"),
    "voice_volume_increase": ControlName("Increase voice-chat volume", "button"),
    "voice_volume_decrease": ControlName("Decrease voice-chat volume", "button"),
    "spotter_volume_increase": ControlName("Increase spotter volume", "button"),
    "spotter_volume_decrease": ControlName("Decrease spotter volume", "button"),
    "spotter_lap_times_toggle": ControlName("Toggle spotter lap times", "button"),
    "spotter_damage_report": ControlName("Request spotter damage report", "button"),
    "spotter_weather_report": ControlName("Request spotter weather report", "button"),
    "master_volume_increase": ControlName("Increase master volume", "button"),
    "master_volume_decrease": ControlName("Decrease master volume", "button"),
    "lfe_volume_increase": ControlName("Increase LFE volume", "button"),
    "lfe_volume_decrease": ControlName("Decrease LFE volume", "button"),
    "trueforce_volume_increase": ControlName("Increase TrueForce volume", "button"),
    "trueforce_volume_decrease": ControlName("Decrease TrueForce volume", "button"),
    "ffb_tone_increase": ControlName("Increase force-feedback tone", "button"),
    "ffb_tone_decrease": ControlName("Decrease force-feedback tone", "button"),
    "optional_vehicle_animation": ControlName("Trigger optional vehicle animation", "button"),
    "alternate_escape": ControlName("Alternate escape", "button"),
    "text_chat_reply": ControlName("Reply in text chat", "button"),
    "text_chat_toggle": ControlName("Toggle text-chat display", "button"),
    "restart_race": ControlName("Restart race", "button"),
    "triples_toggle": ControlName("Toggle triple-screen mode", "button"),
    "auto_shift_mode_increase": ControlName("Increase automatic-shift mode", "button"),
    "auto_shift_mode_decrease": ControlName("Decrease automatic-shift mode", "button"),
    "in_car_menu_toggle": ControlName("Toggle in-car menu", "button"),
}


EXTENDED_CONTROLS: dict[str, ControlName] = {
    "abs_position": ControlName("Set ABS position directly", "button"),
    "front_arb_position": ControlName("Set front anti-roll bar directly", "button"),
    "rear_arb_position": ControlName("Set rear anti-roll bar directly", "button"),
    "turbo_boost_position": ControlName("Set turbo boost directly", "button"),
    "brake_bias_position": ControlName("Set brake bias directly", "button"),
    "brake_bias_fine_position": ControlName("Set fine brake bias directly", "button"),
    "brake_misc_position": ControlName("Set miscellaneous brake value directly", "button"),
    "peak_brake_bias_position": ControlName("Set peak brake bias directly", "button"),
    "dash_page_position": ControlName("Select dashboard page directly", "button"),
    "dash_page_2_position": ControlName("Select secondary dashboard page directly", "button"),
    "diff_preload_position": ControlName("Set differential preload directly", "button"),
    "diff_entry_position": ControlName("Set differential entry directly", "button"),
    "diff_middle_position": ControlName("Set differential mid-corner directly", "button"),
    "diff_exit_position": ControlName("Set differential exit directly", "button"),
    "engine_braking_position": ControlName("Set engine braking directly", "button"),
    "engine_power_position": ControlName("Set engine power directly", "button"),
    "fuel_cut_position": ControlName("Set fuel-cut position directly", "button"),
    "fuel_mixture_position": ControlName("Set fuel mixture directly", "button"),
    "launch_rpm_position": ControlName("Set launch RPM directly", "button"),
    "mguk_fixed_deployment_position": ControlName("Set fixed MGU-K deployment directly", "button"),
    "mguk_deployment_mode_position": ControlName("Set MGU-K deployment mode directly", "button"),
    "mguk_regen_position": ControlName("Set MGU-K regeneration directly", "button"),
    "power_steering_position": ControlName("Set power steering directly", "button"),
    "qualifying_tape_position": ControlName("Set qualifying tape directly", "button"),
    "shock_left_front_position": ControlName("Set left-front shock directly", "button"),
    "shock_right_front_position": ControlName("Set right-front shock directly", "button"),
    "shock_left_rear_position": ControlName("Set left-rear shock directly", "button"),
    "shock_right_rear_position": ControlName("Set right-rear shock directly", "button"),
    "throttle_shape_position": ControlName("Set throttle shaping directly", "button"),
    "tc_position": ControlName("Set traction control directly", "button"),
    "tc_2_position": ControlName("Set traction control 2 directly", "button"),
    "tc_3_position": ControlName("Set traction control 3 directly", "button"),
    "tc_4_position": ControlName("Set traction control 4 directly", "button"),
    "weight_jacker_left_position": ControlName("Set left weight jacker directly", "button"),
    "weight_jacker_right_position": ControlName("Set right weight jacker directly", "button"),
    "front_wing_position": ControlName("Set front wing directly", "button"),
    "rear_wing_position": ControlName("Set rear wing directly", "button"),
    "headlight_stage_direct": ControlName("Select headlight stage directly", "button"),
    "display_device_direct": ControlName("Select display device directly", "button"),
    "tc_cut_position": ControlName("Set traction-control cut directly", "button"),
    "engine_map_position": ControlName("Set engine map directly", "button"),
    "stability_control_position": ControlName("Set stability-control level directly", "button"),
    "wiper_stage_direct": ControlName("Select wiper stage directly", "button"),
    "electronic_brake_balance_increase": ControlName("Increase electronic brake balance", "button"),
    "electronic_brake_balance_decrease": ControlName("Decrease electronic brake balance", "button"),
    **{
        f"black_box_{number}": ControlName(f"Open black box {number}", "button")
        for number in range(1, 13)
    },
    "black_box_size": ControlName("Change black-box size", "button"),
    "black_box_toggle": ControlName("Toggle black box", "button"),
    "custom_sector_start": ControlName("Set custom-sector start", "button"),
    "custom_sector_end": ControlName("Set custom-sector end", "button"),
    "driver_horizon_increase": ControlName("Raise driver horizon", "button"),
    "driver_horizon_decrease": ControlName("Lower driver horizon", "button"),
    "dash_box_toggle": ControlName("Toggle dashboard box", "button"),
    "driver_marker": ControlName("Place driver telemetry marker", "button"),
    "previous_camera": ControlName("Previous driving camera", "button"),
    "camera_view_set": ControlName("Select camera-view set", "button"),
    "qualifying_tape_increase": ControlName("Increase qualifying tape", "button"),
    "qualifying_tape_decrease": ControlName("Decrease qualifying tape", "button"),
    "recenter_tilt_axis": ControlName("Recenter tilt axis", "button"),
    "reload_car_texture": ControlName("Reload car texture", "button"),
    "latency_report": ControlName("Report network latency", "button"),
    "active_reset_save": ControlName("Save active-reset point", "button"),
    "active_reset_run": ControlName("Run active reset", "button"),
    "spotter_leader_line": ControlName("Request spotter leader-line report", "button"),
    "splits_delta_next": ControlName("Next splits-delta mode", "button"),
    "splits_delta_previous": ControlName("Previous splits-delta mode", "button"),
    "layout_edit_toggle": ControlName("Toggle layout editing", "button"),
    "radar_toggle": ControlName("Toggle radar", "button"),
    "reference_car_toggle": ControlName("Toggle reference car", "button"),
    "system_meter_toggle": ControlName("Toggle system meters", "button"),
    "interface_visibility_toggle": ControlName("Toggle interface visibility", "button"),
    "video_capture_toggle": ControlName("Toggle video capture", "button"),
    "video_timer_toggle": ControlName("Toggle video timer", "button"),
    "sdk_logging_toggle": ControlName("Toggle telemetry logging", "button"),
    "giant_screenshot": ControlName("Take giant screenshot", "button"),
    "vr_panel_forward": ControlName("Move VR panel forward", "button"),
    "vr_panel_backward": ControlName("Move VR panel backward", "button"),
    "vr_panel_scale_increase": ControlName("Increase VR-panel scale", "button"),
    "vr_panel_scale_decrease": ControlName("Decrease VR-panel scale", "button"),
    "cpu_time_display": ControlName("Toggle CPU-time display", "button"),
    "framerate_display": ControlName("Toggle framerate display", "button"),
    "camera_zoom_in": ControlName("Camera zoom in", "button"),
    "camera_zoom_out": ControlName("Camera zoom out", "button"),
    "driving_camera_mode": ControlName("Select driving camera", "button"),
    "onboard_camera_mode": ControlName("Select onboard camera", "button"),
    "spectator_camera_mode": ControlName("Select spectator camera", "button"),
    "swingman_camera_mode": ControlName("Select swingman camera", "button"),
    "tracking_camera_mode": ControlName("Select tracking camera", "button"),
    "original_vehicle_view": ControlName("View original vehicle", "button"),
    "instant_replay": ControlName("Start instant replay", "button"),
    "swingman_up": ControlName("Move swingman camera up", "button"),
    "swingman_down": ControlName("Move swingman camera down", "button"),
    "swingman_left": ControlName("Move swingman camera left", "button"),
    "swingman_right": ControlName("Move swingman camera right", "button"),
    "swingman_reset": ControlName("Reset swingman camera", "button"),
    "swingman_zoom_in": ControlName("Swingman camera zoom in", "button"),
    "swingman_zoom_out": ControlName("Swingman camera zoom out", "button"),
}


CAMERA_CONTROLS: dict[str, ControlName] = {
    "camera_altitude_increase": ControlName("Move camera up", "button"),
    "camera_altitude_decrease": ControlName("Move camera down", "button"),
    "camera_lateral_increase": ControlName("Move camera right", "button"),
    "camera_lateral_decrease": ControlName("Move camera left", "button"),
    "camera_longitudinal_increase": ControlName("Move camera forward", "button"),
    "camera_longitudinal_decrease": ControlName("Move camera backward", "button"),
    "camera_yaw_increase": ControlName("Yaw camera right", "button"),
    "camera_yaw_decrease": ControlName("Yaw camera left", "button"),
    "camera_pitch_increase": ControlName("Pitch camera up", "button"),
    "camera_pitch_decrease": ControlName("Pitch camera down", "button"),
    "camera_roll_increase": ControlName("Roll camera right", "button"),
    "camera_roll_decrease": ControlName("Roll camera left", "button"),
    **{
        f"camera_{motion}_{speed}": ControlName(
            f"{label} camera {speed}ly", "button"
        )
        for speed in ("slow", "fast")
        for motion, label in {
            "pan_up": "Pan up",
            "pan_down": "Pan down",
            "pan_left": "Pan left",
            "pan_right": "Pan right",
            "forward": "Move forward",
            "backward": "Move backward",
            "yaw_left": "Yaw left",
            "yaw_right": "Yaw right",
            "pitch_up": "Pitch up",
            "pitch_down": "Pitch down",
            "roll_left": "Roll left",
            "roll_right": "Roll right",
        }.items()
    },
    "drone_camera_toggle": ControlName("Toggle drone camera", "button"),
    "onboard_free_camera": ControlName("Select free onboard camera", "button"),
    "free_camera": ControlName("Select free camera", "button"),
    "camera_view_reset": ControlName("Reset camera view", "button"),
    "camera_view_reset_cancel": ControlName("Cancel camera-view reset", "button"),
    "camera_zoom_toggle": ControlName("Toggle camera zoom", "button"),
    "showroom_rotate_car": ControlName("Rotate showroom car", "button"),
    "showroom_internal_view": ControlName("Select showroom internal view", "button"),
    "focus_next_car": ControlName("Focus next car", "button"),
    "focus_previous_car": ControlName("Focus previous car", "button"),
    "focus_player_car": ControlName("Focus player car", "button"),
}


MEDIA_CONTROLS: dict[str, ControlName] = {
    "camera_acquire_start": ControlName("Start camera acquisition", "button"),
    "camera_acquire_end": ControlName("End camera acquisition", "button"),
    "camera_copy": ControlName("Copy camera", "button"),
    "camera_exposure_increase": ControlName("Increase camera exposure", "button"),
    "camera_exposure_decrease": ControlName("Decrease camera exposure", "button"),
    "camera_f_number_increase": ControlName("Increase camera F-number", "button"),
    "camera_f_number_decrease": ControlName("Decrease camera F-number", "button"),
    "camera_focus_depth_increase": ControlName("Increase camera focus depth", "button"),
    "camera_focus_depth_decrease": ControlName("Decrease camera focus depth", "button"),
    "camera_ir_max_temperature_increase": ControlName("Increase infrared maximum temperature", "button"),
    "camera_ir_max_temperature_decrease": ControlName("Decrease infrared maximum temperature", "button"),
    "camera_ir_min_temperature_increase": ControlName("Increase infrared minimum temperature", "button"),
    "camera_ir_min_temperature_decrease": ControlName("Decrease infrared minimum temperature", "button"),
    "camera_insert": ControlName("Insert camera", "button"),
    "camera_listener_gain_auto": ControlName("Automatically set camera listener gain", "button"),
    "camera_listener_gain_increase": ControlName("Increase camera listener gain", "button"),
    "camera_listener_gain_decrease": ControlName("Decrease camera listener gain", "button"),
    "camera_load_car": ControlName("Load car camera set", "button"),
    "camera_load_track": ControlName("Load track camera set", "button"),
    "camera_move_multiplier_increase": ControlName("Increase camera movement multiplier", "button"),
    "camera_move_multiplier_decrease": ControlName("Decrease camera movement multiplier", "button"),
    "camera_near_plane_increase": ControlName("Increase camera near-plane bias", "button"),
    "camera_near_plane_decrease": ControlName("Decrease camera near-plane bias", "button"),
    "camera_paste": ControlName("Paste camera", "button"),
    "camera_radius_increase": ControlName("Increase camera radius", "button"),
    "camera_radius_decrease": ControlName("Decrease camera radius", "button"),
    "camera_remove": ControlName("Remove camera", "button"),
    "camera_save_car": ControlName("Save car camera set", "button"),
    "camera_save_track": ControlName("Save track camera set", "button"),
    "camera_shake_increase": ControlName("Increase camera shake", "button"),
    "camera_shake_decrease": ControlName("Decrease camera shake", "button"),
    "camera_acquire_toggle": ControlName("Toggle camera acquisition", "button"),
    "camera_aim_type_toggle": ControlName("Cycle camera aim type", "button"),
    "camera_beyond_fence_toggle": ControlName("Toggle camera beyond-fence permission", "button"),
    "camera_control_active_toggle": ControlName("Toggle camera controls", "button"),
    "camera_local_copy_toggle": ControlName("Toggle local camera copy", "button"),
    "camera_tool_toggle": ControlName("Toggle camera tool", "button"),
    "camera_display_toggle": ControlName("Toggle camera display", "button"),
    "camera_focus_toggle": ControlName("Toggle camera focus", "button"),
    "camera_weight_toggle": ControlName("Toggle weighted camera movement", "button"),
    "camera_in_cockpit_toggle": ControlName("Toggle in-cockpit camera state", "button"),
    "camera_infrared_toggle": ControlName("Toggle infrared camera mode", "button"),
    "camera_move_acceleration_toggle": ControlName("Toggle camera movement acceleration", "button"),
    "camera_move_scale_toggle": ControlName("Toggle camera movement scaling", "button"),
    "camera_parabolic_microphone_toggle": ControlName("Toggle parabolic microphone", "button"),
    "camera_pitch_gyro_toggle": ControlName("Toggle camera pitch gyro", "button"),
    "camera_position_type_toggle": ControlName("Cycle camera position type", "button"),
    "camera_roll_gyro_toggle": ControlName("Toggle camera roll gyro", "button"),
    "camera_sensor_type_toggle": ControlName("Cycle camera sensor type", "button"),
    "camera_shot_queue_toggle": ControlName("Toggle camera shot queue", "button"),
    "camera_vanishing_point_x_increase": ControlName("Move camera vanishing point right", "button"),
    "camera_vanishing_point_x_decrease": ControlName("Move camera vanishing point left", "button"),
    "camera_vanishing_point_y_increase": ControlName("Move camera vanishing point up", "button"),
    "camera_vanishing_point_y_decrease": ControlName("Move camera vanishing point down", "button"),
    "camera_velocity_increase": ControlName("Increase camera velocity", "button"),
    "camera_velocity_decrease": ControlName("Decrease camera velocity", "button"),
    "camera_group_copy": ControlName("Copy camera group", "button"),
    "camera_group_paste": ControlName("Paste camera group", "button"),
    "replay_next_camera": ControlName("Next replay camera", "button"),
    "replay_previous_camera": ControlName("Previous replay camera", "button"),
    "replay_next_camera_group": ControlName("Next replay camera group", "button"),
    "replay_previous_camera_group": ControlName("Previous replay camera group", "button"),
    "replay_fast_forward": ControlName("Fast-forward replay", "button"),
    "replay_frame_advance": ControlName("Advance replay one frame", "button"),
    "replay_frame_rewind": ControlName("Rewind replay one frame", "button"),
    "replay_next_incident": ControlName("Seek to next incident", "button"),
    "replay_previous_incident": ControlName("Seek to previous incident", "button"),
    "replay_rate_increase": ControlName("Increase replay speed", "button"),
    "replay_next_lap": ControlName("Seek to next lap", "button"),
    "replay_previous_lap": ControlName("Seek to previous lap", "button"),
    "replay_pause_play": ControlName("Pause or play replay", "button"),
    "replay_rewind": ControlName("Rewind replay", "button"),
    "replay_next_session": ControlName("Seek to next session", "button"),
    "replay_previous_session": ControlName("Seek to previous session", "button"),
    "replay_stop": ControlName("Stop replay", "button"),
    "replay_to_end": ControlName("Jump to replay end", "button"),
    "replay_to_start": ControlName("Jump to replay start", "button"),
}


CONTROL_BATCHES = {
    "basic_driving": tuple(BASIC_CONTROLS),
    "common_race": tuple(COMMON_CONTROLS),
    "car_setup_and_cockpit": tuple(ADVANCED_CONTROLS),
    "advanced_tuning_and_race_ops": tuple(TUNING_CONTROLS),
    "suspension_hybrid_and_communications": tuple(SYSTEM_CONTROLS),
    "remaining_core_and_utility": tuple(UTILITY_CONTROLS),
    "positional_and_extended_user_controls": tuple(EXTENDED_CONTROLS),
    "camera_movement_and_selection": tuple(CAMERA_CONTROLS),
    "advanced_camera_and_replay": tuple(MEDIA_CONTROLS),
}


CONTROLS = {
    **BASIC_CONTROLS,
    **COMMON_CONTROLS,
    **ADVANCED_CONTROLS,
    **TUNING_CONTROLS,
    **SYSTEM_CONTROLS,
    **UTILITY_CONTROLS,
    **EXTENDED_CONTROLS,
    **CAMERA_CONTROLS,
    **MEDIA_CONTROLS,
}


def _native(
    *names: str,
    status: MappingStatus = "exact",
    note: str = "",
) -> NativeControlName:
    return NativeControlName(names, status, note)


def _missing(status: Literal["not_exposed", "not_observed"], note: str) -> NativeControlName:
    return NativeControlName(status=status, note=note)


BASIC_NATIVE_CONTROL_NAMES: dict[str, dict[str, NativeControlName]] = {
    "iracing": {
        "steering": _native("SteerLeft", "SteerRight", note="Paired steering records."),
        "accelerator": _native("Throttle", "Throttle2", note="Primary and secondary slots."),
        "brake": _native("Brake", "Brake2", note="Primary and secondary slots."),
        "clutch": _native("Clutch", "Clutch2", note="Primary and secondary slots."),
        "shift_up": _native("ShiftUp", "ShiftUp2", note="Primary and secondary slots."),
        "shift_down": _native("ShiftDown", "ShiftDown2", note="Primary and secondary slots."),
        "reverse_gear": _native("GearReverse"),
        "neutral_gear": _native("GearNeutral"),
        **{f"gear_{number}": _native(f"Gear{number}") for number in range(1, 10)},
        "handbrake": _native("Handbrake"),
        "ignition": _native("Ignition"),
        "starter": _native("Starter"),
        "pit_limiter": _native("PitSpeedLimiter"),
    },
    "assetto_corsa": {
        "steering": _native("[STEER]"),
        "accelerator": _native("[THROTTLE]"),
        "brake": _native("[BRAKES]"),
        "clutch": _native("[CLUTCH]"),
        "shift_up": _native("[GEARUP]"),
        "shift_down": _native("[GEARDN]"),
        "reverse_gear": _native("[SHIFTER] GEAR_R"),
        "neutral_gear": _missing(
            "not_exposed", "No distinct neutral field exists in the installed controls.ini."
        ),
        **{
            f"gear_{number}": _native(f"[SHIFTER] GEAR_{number}")
            for number in range(1, 8)
        },
        "gear_8": _missing("not_exposed", "The installed SHIFTER section ends at gear 7."),
        "gear_9": _missing("not_exposed", "The installed SHIFTER section ends at gear 7."),
        "handbrake": _native("[HANDBRAKE]"),
        "ignition": _missing(
            "not_exposed", "No ignition action section exists in the installed controls.ini."
        ),
        "starter": _native("[STARTER]"),
        "pit_limiter": _missing(
            "not_exposed", "No pit-limiter action section exists in the installed controls.ini."
        ),
    },
    "assetto_corsa_competizione": {
        "steering": _native("Steer"),
        "accelerator": _native("Gas"),
        "brake": _native("Brake"),
        "clutch": _native("Clutch"),
        "shift_up": _native("GearUp"),
        "shift_down": _native("GearDown"),
        "reverse_gear": _missing(
            "not_observed", "No reverse action was present in the inspected controls.json."
        ),
        "neutral_gear": _missing(
            "not_observed", "No neutral action was present in the inspected controls.json."
        ),
        **{
            f"gear_{number}": _missing(
                "not_observed", "No direct-gear action was present in the inspected controls.json."
            )
            for number in range(1, 10)
        },
        "handbrake": _missing(
            "not_observed", "No handbrake action was present in the inspected controls.json."
        ),
        "ignition": _native(
            "IgnitionOff",
            "IgnitionSequenceOn",
            status="compound",
            note="ACC exposes separate off and start-sequence commands, not one ignition toggle.",
        ),
        "starter": _native("Starter"),
        "pit_limiter": _native("PitLimiter"),
    },
    "assetto_corsa_evo": {
        "steering": _native("100: InputAction_Car_Steer_Left", "101: InputAction_Car_Steer_Right"),
        "accelerator": _native("102: InputAction_Car_Gas"),
        "brake": _native("103: InputAction_Car_Brake"),
        "clutch": _native("105: InputAction_Car_Clutch"),
        "shift_up": _native(
            "110: InputAction_Car_Paddle_Gear_X_2",
            status="compound",
            note="Packed two-way action; the up/down sub-action encoding is not yet decoded.",
        ),
        "shift_down": _native(
            "110: InputAction_Car_Paddle_Gear_X_2",
            status="compound",
            note="Packed two-way action; the up/down sub-action encoding is not yet decoded.",
        ),
        "reverse_gear": _native("113: InputAction_Car_Shifter_Gear_Reverse"),
        "neutral_gear": _missing(
            "not_observed", "The installed InputAction enum has no distinct neutral identifier."
        ),
        **{
            f"gear_{number}": _native(
                "111: InputAction_Car_Shifter_Gear_X_9",
                status="compound",
                note="Packed nine-way action; direct-gear sub-action indices are not yet decoded.",
            )
            for number in range(1, 10)
        },
        "handbrake": _native("104: InputAction_Car_Handbrake"),
        "ignition": _native("136: InputAction_Car_Ignition_Toggle"),
        "starter": _native("137: InputAction_Car_Starter"),
        "pit_limiter": _native("138: InputAction_Car_Pit_Limiter_Toggle"),
    },
    "automobilista_2": {
        "steering": _native("Steer Left", "Steer Right"),
        "accelerator": _native("Accelerate"),
        "brake": _native("Brake"),
        "clutch": _native("Clutch"),
        "shift_up": _native("Shift Up"),
        "shift_down": _native("Shift Down"),
        "reverse_gear": _native("Gear R"),
        "neutral_gear": _missing(
            "not_observed", "No distinct neutral label was found in the installed executable."
        ),
        **{f"gear_{number}": _native(f"Gear {number}") for number in range(1, 10)},
        "handbrake": _native("Handbrake"),
        "ignition": _native("Toggle Ignition"),
        "starter": _native("Start Your Engine"),
        "pit_limiter": _native("Toggle Pit Speed Limiter"),
    },
    "le_mans_ultimate": {
        "steering": _native("Steer Left", "Steer Right"),
        "accelerator": _native("Throttle"),
        "brake": _native("Brake"),
        "clutch": _native("Clutch In"),
        "shift_up": _native("Shift Up"),
        "shift_down": _native("Shift Down"),
        "reverse_gear": _native("Reverse Gear"),
        "neutral_gear": _native("Neutral"),
        "gear_1": _native("First Gear"),
        "gear_2": _native("Second Gear"),
        "gear_3": _native("Third Gear"),
        "gear_4": _native("Fourth Gear"),
        "gear_5": _native("Fifth Gear"),
        "gear_6": _native("Sixth Gear"),
        **{
            f"gear_{number}": _missing(
                "not_exposed", "The installed preset vocabulary ends at sixth gear."
            )
            for number in range(7, 10)
        },
        "handbrake": _missing(
            "not_exposed", "No handbrake action exists in the installed preset vocabulary."
        ),
        "ignition": _native("Ignition"),
        "starter": _native("Starter"),
        "pit_limiter": _native("Speed Limiter"),
    },
}


COMMON_NATIVE_CONTROL_NAMES: dict[str, dict[str, NativeControlName]] = {
    "iracing": {
        "headlights": _missing(
            "not_exposed", "No headlight cycle/toggle exists in the complete action table."
        ),
        "headlights_flash": _native("HeadlightFlash"),
        "wipers": _native("ToggleWindshieldWipers"),
        "horn": _missing("not_exposed", "No horn exists in the complete action table."),
        "look_left": _native("LookLeft"),
        "look_right": _native("LookRight"),
        "look_rear": _missing(
            "not_exposed", "No distinct look-behind action exists in the complete action table."
        ),
        "next_camera": _native("NextDrivingCam"),
        "brake_bias_increase": _native("BrakeBiasInc"),
        "brake_bias_decrease": _native("BrakeBiasDec"),
        "tc_increase": _native("TractionControlInc"),
        "tc_decrease": _native("TractionControlDec"),
        "tc_toggle": _native("TractionControlToggle"),
        "abs_increase": _native("ABSInc"),
        "abs_decrease": _native("ABSDec"),
        "abs_toggle": _native("ABSToggle"),
        "drs": _native("DRS"),
        "overtake": _native("PushToPass"),
        "reset_car": _native("Reset"),
        "pause": _native("Pause"),
    },
    "assetto_corsa": {
        "headlights": _native("[ACTION_HEADLIGHTS]"),
        "headlights_flash": _native("[ACTION_HEADLIGHTS_FLASH]"),
        "wipers": _missing(
            "not_exposed", "No wiper action section exists in the installed controls.ini."
        ),
        "horn": _native("[ACTION_HORN]"),
        "look_left": _native("[GLANCELEFT]"),
        "look_right": _native("[GLANCERIGHT]"),
        "look_rear": _native("[GLANCEBACK]"),
        "next_camera": _native("[ACTION_CHANGE_CAMERA]"),
        "brake_bias_increase": _native("[BALANCEUP]"),
        "brake_bias_decrease": _native("[BALANCEDN]"),
        "tc_increase": _native("[TCUP]"),
        "tc_decrease": _native("[TCDN]"),
        "tc_toggle": _missing(
            "not_exposed", "No traction-control toggle section exists in controls.ini."
        ),
        "abs_increase": _native("[ABSUP]"),
        "abs_decrease": _native("[ABSDN]"),
        "abs_toggle": _missing(
            "not_exposed", "No ABS toggle section exists in controls.ini."
        ),
        "drs": _native("[DRS]"),
        "overtake": _native(
            "[KERS]",
            status="related",
            note="KERS activation is related to, but not universally equivalent to, overtake mode.",
        ),
        "reset_car": _missing(
            "not_exposed", "No reset-car action section exists in controls.ini."
        ),
        "pause": _missing(
            "not_exposed", "No pause action section exists in controls.ini."
        ),
    },
    "assetto_corsa_competizione": {
        "headlights": _native("CycleCarLightStages"),
        "headlights_flash": _missing(
            "not_observed", "No flash action was present in the inspected controls.json."
        ),
        "wipers": _native("CycleWiper"),
        "horn": _missing(
            "not_observed", "No horn action was present in the inspected controls.json."
        ),
        "look_left": _native("LookLeft"),
        "look_right": _native("LookRight"),
        "look_rear": _missing(
            "not_observed", "No look-behind action was present in the inspected controls.json."
        ),
        "next_camera": _native("CycleCamera"),
        "brake_bias_increase": _native("IncreaseBrakeBias"),
        "brake_bias_decrease": _native("DecreaseBrakeBias"),
        "tc_increase": _native("IncreaseTC"),
        "tc_decrease": _native("DecreaseTC"),
        "tc_toggle": _missing(
            "not_observed", "No TC toggle was present in the inspected controls.json."
        ),
        "abs_increase": _missing(
            "not_observed", "No ABS adjustment was present in the inspected controls.json."
        ),
        "abs_decrease": _missing(
            "not_observed", "No ABS adjustment was present in the inspected controls.json."
        ),
        "abs_toggle": _missing(
            "not_observed", "No ABS toggle was present in the inspected controls.json."
        ),
        "drs": _missing(
            "not_observed", "No DRS action was present in the inspected controls.json."
        ),
        "overtake": _missing(
            "not_observed", "No overtake action was present in the inspected controls.json."
        ),
        "reset_car": _missing(
            "not_observed", "No reset-car action was present in the inspected controls.json."
        ),
        "pause": _native("Pause"),
    },
    "assetto_corsa_evo": {
        "headlights": _native(
            "120: InputAction_Car_Light_Cycle_X_2",
            status="compound",
            note="Packed two-way light-cycle action; sub-action encoding is not decoded.",
        ),
        "headlights_flash": _native("121: InputAction_Car_Flashing_Lights"),
        "wipers": _native(
            "155: InputAction_Car_Wipers_Cycle_X_2",
            status="compound",
            note="Packed two-way wiper-cycle action; sub-action encoding is not decoded.",
        ),
        "horn": _native("139: InputAction_Car_Horn"),
        "look_left": _native("425: InputAction_Camera_LookLeft"),
        "look_right": _native("426: InputAction_Camera_LookRight"),
        "look_rear": _native("427: InputAction_Camera_LookBehind"),
        "next_camera": _native(
            "405: InputAction_Camera_Sequence",
            status="related",
            note="The installed name suggests sequencing cameras; in-game cycle behavior is unverified.",
        ),
        "brake_bias_increase": _native(
            "148: InputAction_Car_Brake_Bias_Cycle_X_2",
            status="compound",
            note="Packed two-way action; forward/rearward sub-action encoding is not decoded.",
        ),
        "brake_bias_decrease": _native(
            "148: InputAction_Car_Brake_Bias_Cycle_X_2",
            status="compound",
            note="Packed two-way action; forward/rearward sub-action encoding is not decoded.",
        ),
        "tc_increase": _native(
            "140: InputAction_Car_TractionControl_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease sub-action encoding is not decoded.",
        ),
        "tc_decrease": _native(
            "140: InputAction_Car_TractionControl_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease sub-action encoding is not decoded.",
        ),
        "tc_toggle": _missing(
            "not_exposed", "The installed enum exposes cycle/direct TC actions, not a toggle."
        ),
        "abs_increase": _native(
            "144: InputAction_Car_ABS_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease sub-action encoding is not decoded.",
        ),
        "abs_decrease": _native(
            "144: InputAction_Car_ABS_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease sub-action encoding is not decoded.",
        ),
        "abs_toggle": _missing(
            "not_exposed", "The installed enum exposes cycle/direct ABS actions, not a toggle."
        ),
        "drs": _native("1704: InputAction_Car_DRS_Toggle"),
        "overtake": _native("1703: InputAction_Car_Ers_Overtake"),
        "reset_car": _native(
            "525: InputAction_UI_FreeRoamCarReset",
            status="related",
            note="This identifier is specifically a free-roam reset, not a general race reset.",
        ),
        "pause": _missing(
            "not_exposed", "No distinct pause identifier exists in the installed enum."
        ),
    },
    "automobilista_2": {
        "headlights": _native("HeadLights"),
        "headlights_flash": _native(
            "High Beam",
            status="related",
            note="High-beam control is related to, but may not behave as, a momentary flash.",
        ),
        "wipers": _native("Wipers"),
        "horn": _missing(
            "not_exposed", "No horn label was found in the installed executable."
        ),
        "look_left": _native("Look Left"),
        "look_right": _native("Look Right"),
        "look_rear": _native("Look Back"),
        "next_camera": _native("Change View", "Cycle Cam Forward"),
        "brake_bias_increase": _native("Increase Brake Bias"),
        "brake_bias_decrease": _native("Decrease Brake Bias"),
        "tc_increase": _native("Onboard Traction Control Increase"),
        "tc_decrease": _native("Onboard Traction Control Decrease"),
        "tc_toggle": _native("Toggle Traction Control"),
        "abs_increase": _native("Increase Abs Strength"),
        "abs_decrease": _native("Decrease Abs Strength"),
        "abs_toggle": _native("Toggle ABS"),
        "drs": _native("DRS"),
        "overtake": _native("ERS Mode Overtake"),
        "reset_car": _native("Reset Car"),
        "pause": _native("Pause Game"),
    },
    "le_mans_ultimate": {
        "headlights": _native("Headlights"),
        "headlights_flash": _native("Headlights Pulse"),
        "wipers": _native("Wipers"),
        "horn": _native("Horn"),
        "look_left": _native("Look Left"),
        "look_right": _native("Look Right"),
        "look_rear": _native("Rear Look"),
        "next_camera": _native("Push To change camera view"),
        "brake_bias_increase": _native("Bias Forward"),
        "brake_bias_decrease": _native("Bias Rearward"),
        "tc_increase": _native("Traction Control Up"),
        "tc_decrease": _native("Traction Control Down"),
        "tc_toggle": _missing(
            "not_exposed", "No traction-control toggle exists in the preset vocabulary."
        ),
        "abs_increase": _native("Antilock Brake System Up"),
        "abs_decrease": _native("Antilock Brake System Down"),
        "abs_toggle": _missing(
            "not_exposed", "No ABS toggle exists in the preset vocabulary."
        ),
        "drs": _native(
            "Rear Flap", note="The installed rFactor-derived vocabulary calls DRS Rear Flap."
        ),
        "overtake": _missing(
            "not_exposed", "No distinct overtake or push-to-pass action exists in presets."
        ),
        "reset_car": _missing(
            "not_exposed", "Restart Race is not equivalent to resetting only the car."
        ),
        "pause": _missing(
            "not_exposed", "No distinct pause action exists in the preset vocabulary."
        ),
    },
}


_ADVANCED_NATIVE_OVERRIDES: dict[str, dict[str, NativeControlName]] = {
    "iracing": {
        "fuel_mixture_increase": _native("FuelMixtureInc"),
        "fuel_mixture_decrease": _native("FuelMixtureDec"),
        "engine_map_increase": _native(
            "EnginePowerInc",
            status="related",
            note="Engine power is related to, but may not equal, a numbered engine map.",
        ),
        "engine_map_decrease": _native(
            "EnginePowerDec",
            status="related",
            note="Engine power is related to, but may not equal, a numbered engine map.",
        ),
        "engine_braking_increase": _native("EngineBrakingInc"),
        "engine_braking_decrease": _native("EngineBrakingDec"),
        "turbo_boost_increase": _native("BoostLevelInc"),
        "turbo_boost_decrease": _native("BoostLevelDec"),
        "front_arb_increase": _native("AntiRollFrontInc"),
        "front_arb_decrease": _native("AntiRollFrontDec"),
        "rear_arb_increase": _native("AntiRollRearInc"),
        "rear_arb_decrease": _native("AntiRollRearDec"),
        "weight_jacker_increase": _native(
            "WeightJackerLeftInc",
            "WeightJackerRightInc",
            status="compound",
            note="iRacing exposes separate left and right weight-jacker commands.",
        ),
        "weight_jacker_decrease": _native(
            "WeightJackerLeftDec",
            "WeightJackerRightDec",
            status="compound",
            note="iRacing exposes separate left and right weight-jacker commands.",
        ),
        "ers_deployment_increase": _native("MGUKDeployModeInc"),
        "ers_deployment_decrease": _native("MGUKDeployModeDec"),
        "ers_regen_increase": _native("MGUKRegenGainInc"),
        "ers_regen_decrease": _native("MGUKRegenGainDec"),
        "launch_control": _native(
            "ClutchLaunchAssist",
            status="related",
            note="Clutch launch assist is not necessarily a general launch-control toggle.",
        ),
        "mfd_next": _native(
            "BlackBoxShowNext",
            status="related",
            note="iRacing calls its multifunction displays black boxes.",
        ),
        "mfd_previous": _native(
            "BlackBoxShowPrev",
            status="related",
            note="iRacing calls its multifunction displays black boxes.",
        ),
        "hud_toggle": _native(
            "ToggleUIVisibleDrive",
            status="related",
            note="This toggles the driving UI as a whole, not only a HUD layer.",
        ),
        "dash_page_next": _native("DashPageInc"),
        "dash_page_previous": _native("DashPageDec"),
        "pit_menu_up": _native(
            "BlackBoxPrev",
            status="related",
            note="Black-box navigation is not limited to the pit menu.",
        ),
        "pit_menu_down": _native(
            "BlackBoxNext",
            status="related",
            note="Black-box navigation is not limited to the pit menu.",
        ),
        "pit_menu_increase": _native(
            "BlackBoxInc",
            status="related",
            note="Black-box adjustment is not limited to the pit menu.",
        ),
        "pit_menu_decrease": _native(
            "BlackBoxDec",
            status="related",
            note="Black-box adjustment is not limited to the pit menu.",
        ),
        "driving_aids": _native(
            "ToggleDrivingLine",
            status="related",
            note="This toggles only the driving line, not a general aids cycle.",
        ),
        "ffb_gain_increase": _native("IncFFB"),
        "ffb_gain_decrease": _native("DecFFB"),
        "seat_up": _native(
            "DCamDrvHeightInc",
            status="related",
            note="This adjusts driver-camera height rather than a physical seat model.",
        ),
        "seat_down": _native(
            "DCamDrvHeightDec",
            status="related",
            note="This adjusts driver-camera height rather than a physical seat model.",
        ),
        "fov_increase": _native("DCamFOVInc"),
        "fov_decrease": _native("DCamFOVDec"),
        "virtual_mirror_toggle": _native("ToggleVirtualMirror"),
        "push_to_talk": _native("VChatPushToTalk"),
        "screenshot": _native("TriggerScreenshotCapture"),
        "recenter_vr": _native("RecenterHeadMountedDisplay"),
        "tearoff_visor": _native("TearOffVisor"),
        "rev_limiter": _native("RevLimiter"),
    },
    "assetto_corsa": {
        "engine_braking_increase": _native("[ENGINE_BRAKE_UP]"),
        "engine_braking_decrease": _native("[ENGINE_BRAKE_DN]"),
        "turbo_boost_increase": _native("[TURBOUP]"),
        "turbo_boost_decrease": _native("[TURBODN]"),
        "ers_deployment_increase": _native("[MGUK_DELIVERY_UP]"),
        "ers_deployment_decrease": _native("[MGUK_DELIVERY_DN]"),
        "ers_regen_increase": _native("[MGUK_RECOVERY_UP]"),
        "ers_regen_decrease": _native("[MGUK_RECOVERY_DN]"),
    },
    "assetto_corsa_competizione": {
        "mfd_next": _native("CycleHudMfd"),
        "dash_page_next": _native("DisplayPageUp"),
        "dash_page_previous": _native("DisplayPageDown"),
    },
    "assetto_corsa_evo": {
        "engine_map_increase": _native(
            "146: InputAction_Car_Engine_Map_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "engine_map_decrease": _native(
            "146: InputAction_Car_Engine_Map_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "turbo_boost_increase": _native(
            "169: InputAction_Car_Turbo_Level_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "turbo_boost_decrease": _native(
            "169: InputAction_Car_Turbo_Level_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "ers_deployment_increase": _native(
            "1701: InputAction_Car_Ers_Deployment_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "ers_deployment_decrease": _native(
            "1701: InputAction_Car_Ers_Deployment_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "ers_regen_increase": _native(
            "1700: InputAction_Car_Ers_Recharge_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "ers_regen_decrease": _native(
            "1700: InputAction_Car_Ers_Recharge_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "rain_light": _native("131: InputAction_Car_Rain_Lights"),
        "indicator_left": _native("132: InputAction_Car_Direction_Light_Left"),
        "indicator_right": _native("133: InputAction_Car_Direction_Light_Right"),
        "hazard_lights": _native("134: InputAction_Car_Warning_Lights"),
        "mfd_next": _native("521: InputAction_UI_Cycle_Mfd_Up"),
        "mfd_previous": _native("522: InputAction_UI_Cycle_Mfd_Down"),
        "hud_toggle": _native("520: InputAction_UI_ToggleHud"),
        "dash_page_next": _native(
            "125: InputAction_Car_Display_Page_Cycle_X_2",
            status="compound",
            note="Packed two-way action; next/previous encoding is not decoded.",
        ),
        "dash_page_previous": _native(
            "125: InputAction_Car_Display_Page_Cycle_X_2",
            status="compound",
            note="Packed two-way action; next/previous encoding is not decoded.",
        ),
        "ffb_gain_increase": _native(
            "168: InputAction_Car_FFB_Gain_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "ffb_gain_decrease": _native(
            "168: InputAction_Car_FFB_Gain_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "fov_increase": _native(
            "435: InputAction_Camera_FovModifier",
            status="related",
            note="A modifier is not a discrete increase command.",
        ),
        "fov_decrease": _native(
            "435: InputAction_Camera_FovModifier",
            status="related",
            note="A modifier is not a discrete decrease command.",
        ),
        "virtual_mirror_toggle": _native("167: InputAction_UI_Toggle_Virtual_Mirror"),
        "driver_labels_toggle": _native("159: InputAction_UI_CycleNameplateVisibility"),
        "recenter_vr": _native(
            "535: InputAction_UI_Vr_Settings_Reset",
            status="related",
            note="This resets VR settings; it may be broader than recentering the view.",
        ),
        "hud_cycle": _native(
            "123: InputAction_Car_Display_Device_Cycle_X_2",
            status="compound",
            note="Packed display-device action; direction encoding is not decoded.",
        ),
    },
    "automobilista_2": {
        "engine_map_increase": _native(
            "Increase Fuel Mapping",
            status="related",
            note="Fuel mapping may not be equivalent to every game's engine-map scale.",
        ),
        "engine_map_decrease": _native(
            "Decrease Fuel Mapping",
            status="related",
            note="Fuel mapping may not be equivalent to every game's engine-map scale.",
        ),
        "turbo_boost_increase": _native("Increase Turbo Boost"),
        "turbo_boost_decrease": _native("Decrease Turbo Boost"),
        "front_arb_increase": _native("Increase Front Anti Roll Bars"),
        "front_arb_decrease": _native("Decrease Front Anti Roll Bars"),
        "rear_arb_increase": _native("Increase Rear Anti Roll Bars"),
        "rear_arb_decrease": _native("Decrease Rear Anti Roll Bars"),
        "weight_jacker_increase": _native("Increase Weight Jacker"),
        "weight_jacker_decrease": _native("Decrease Weight Jacker"),
        "ers_deployment_increase": _native("ERS Mode Increase"),
        "ers_deployment_decrease": _native("ERS Mode Decrease"),
        "launch_control": _native("Launch Control"),
        "mfd_next": _native("ICM Cycle"),
        "hud_toggle": _native("Toggle HUD Dials"),
        "dash_page_next": _native(
            "Cycle Lap Info",
            status="related",
            note="Lap-info cycling is narrower than general dashboard-page navigation.",
        ),
        "pit_request": _native("Request Pit Stop"),
        "pit_menu_up": _native("ICM Up"),
        "pit_menu_down": _native("ICM Down"),
        "pit_menu_increase": _native("ICM Right"),
        "pit_menu_decrease": _native("ICM Left"),
        "driving_aids": _native("Driving Aids"),
        "ffb_gain_increase": _native(
            "Increase Force Feedback Volume",
            status="related",
            note="The installed label says volume rather than gain.",
        ),
        "ffb_gain_decrease": _native(
            "Decrease Force Feedback Volume",
            status="related",
            note="The installed label says volume rather than gain.",
        ),
        "seat_up": _native("Seat Up"),
        "seat_down": _native("Seat Down"),
        "seat_forward": _native("Seat Fore"),
        "seat_backward": _native("Seat Aft"),
        "fov_increase": _native("Increase FOV"),
        "fov_decrease": _native("Reduce FOV"),
        "driver_labels_toggle": _native("Opponent Names Toggle"),
        "recenter_vr": _native("Reset VR"),
        "hud_cycle": _native("Cycle HUD Mode", "HUD Mode"),
    },
    "le_mans_ultimate": {
        "fuel_mixture_increase": _native("Increment Mixture"),
        "fuel_mixture_decrease": _native("Decrement Mixture"),
        "engine_map_increase": _native("Increment Motor Map"),
        "engine_map_decrease": _native("Decrement Motor Map"),
        "front_arb_increase": _native("Inc Front ARB"),
        "front_arb_decrease": _native("Dec Front ARB"),
        "rear_arb_increase": _native("Inc Rear ARB"),
        "rear_arb_decrease": _native("Dec Rear ARB"),
        "ers_regen_increase": _native("Increment Regeneration"),
        "ers_regen_decrease": _native("Decrement Regeneration"),
        "launch_control": _native("Launch Control"),
        "mfd_next": _native("Driver Overlay Next MFD"),
        "mfd_previous": _native("Driver Overlay Previous MFD"),
        "hud_toggle": _native("Driver Overlay Toggle HUD"),
        "pit_request": _native("Pit Request"),
        "pit_menu_up": _native("Pit Menu Up"),
        "pit_menu_down": _native("Pit Menu Down"),
        "pit_menu_increase": _native("Pit Menu Inc"),
        "pit_menu_decrease": _native("Pit Menu Dec"),
        "seat_up": _native("Adjust Seat Up"),
        "seat_down": _native("Adjust Seat Down"),
        "seat_forward": _native("Adjust Seat Fore"),
        "seat_backward": _native("Adjust Seat Aft"),
        "fov_increase": _native("Increase Vertical FOV"),
        "fov_decrease": _native("Decrease Vertical FOV"),
        "virtual_mirror_toggle": _native("Toggle Mirror"),
        "driver_labels_toggle": _native("Display Vehicle Labels"),
        "screenshot": _native("Screenshot"),
        "hud_cycle": _native(
            "Display Mode",
            status="related",
            note="Display Mode may cycle more than the driving HUD presentation.",
        ),
    },
}


ADVANCED_NATIVE_CONTROL_NAMES: dict[str, dict[str, NativeControlName]] = {
    game_id: {
        **{
            control_id: _missing(
                "not_observed" if game_id == "assetto_corsa_competizione" else "not_exposed",
                (
                    "No matching action was present in the inspected binding-dependent "
                    "controls.json."
                    if game_id == "assetto_corsa_competizione"
                    else "No matching identifier was found in the installed action vocabulary."
                ),
            )
            for control_id in ADVANCED_CONTROLS
        },
        **_ADVANCED_NATIVE_OVERRIDES[game_id],
    }
    for game_id in GAMES
}


_TUNING_NATIVE_OVERRIDES: dict[str, dict[str, NativeControlName]] = {
    "iracing": {
        "brake_bias_fine_increase": _native("BrakeBiasFineInc"),
        "brake_bias_fine_decrease": _native("BrakeBiasFineDec"),
        "peak_brake_bias_increase": _native("PeakBrakeBiasInc"),
        "peak_brake_bias_decrease": _native("PeakBrakeBiasDec"),
        "tc_2_increase": _native("TractionControl2Inc"),
        "tc_2_decrease": _native("TractionControl2Dec"),
        "tc_override": _native(
            "TractionControlArm",
            status="related",
            note="Arming traction control is not necessarily a momentary TC override.",
        ),
        "diff_preload_increase": _native("DiffPreloadInc"),
        "diff_preload_decrease": _native("DiffPreloadDec"),
        "diff_entry_increase": _native("DiffEntryInc"),
        "diff_entry_decrease": _native("DiffEntryDec"),
        "diff_middle_increase": _native("DiffMiddleInc"),
        "diff_middle_decrease": _native("DiffMiddleDec"),
        "diff_exit_increase": _native("DiffExitInc"),
        "diff_exit_decrease": _native("DiffExitDec"),
        "front_wing_increase": _native("WingFrontInc"),
        "front_wing_decrease": _native("WingFrontDec"),
        "rear_wing_increase": _native("WingRearInc"),
        "rear_wing_decrease": _native("WingRearDec"),
        "power_steering_increase": _native("PowerSteeringInc"),
        "power_steering_decrease": _native("PowerSteeringDec"),
        "throttle_shape_increase": _native("ThrottleShapeInc"),
        "throttle_shape_decrease": _native("ThrottleShapeDec"),
        "engine_power_increase": _native("EnginePowerInc"),
        "engine_power_decrease": _native("EnginePowerDec"),
        "fuel_cut_increase": _native("FuelCutPositionInc"),
        "fuel_cut_decrease": _native("FuelCutPositionDec"),
        "launch_rpm_increase": _native("LaunchRPMInc"),
        "launch_rpm_decrease": _native("LaunchRPMDec"),
        "single_wipe": _native("TriggerWindshieldWipers"),
        "low_fuel_acknowledge": _native("LowFuelAccept"),
        "in_lap_toggle": _native("InLapToggle"),
        "full_course_yellow": _native("FCYToggle"),
        "fuel_to_end_toggle": _native("FuelToEndToggle"),
        "fuel_to_end_margin_increase": _native("FuelToEndMarginInc"),
        "fuel_to_end_margin_decrease": _native("FuelToEndMarginDec"),
    },
    "assetto_corsa": {},
    "assetto_corsa_competizione": {
        "single_wipe": _native(
            "CycleWiper",
            status="related",
            note="Cycling the wiper state is not a dedicated single-wipe command.",
        ),
    },
    "assetto_corsa_evo": {
        "tc_cut_increase": _native(
            "142: InputAction_Car_TractionControl_Cut_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "tc_cut_decrease": _native(
            "142: InputAction_Car_TractionControl_Cut_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "diff_power_increase": _native(
            "236: InputAction_Car_Diff_Power_Level_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "diff_power_decrease": _native(
            "236: InputAction_Car_Diff_Power_Level_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "diff_coast_increase": _native(
            "237: InputAction_Car_Diff_Coast_Level_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "diff_coast_decrease": _native(
            "237: InputAction_Car_Diff_Coast_Level_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "engine_power_increase": _native(
            "165: InputAction_Car_PerformanceMode_Cycle_X_2",
            status="related",
            note="Performance mode may affect more than engine power.",
        ),
        "engine_power_decrease": _native(
            "165: InputAction_Car_PerformanceMode_Cycle_X_2",
            status="related",
            note="Performance mode may affect more than engine power.",
        ),
        "single_wipe": _native(
            "155: InputAction_Car_Wipers_Cycle_X_2",
            status="related",
            note="A packed wiper-cycle action is not a dedicated single wipe.",
        ),
    },
    "automobilista_2": {
        "diff_preload_increase": _native("Onboard Diff Preload Increase"),
        "diff_preload_decrease": _native("Onboard Diff Preload Decrease"),
        "diff_power_increase": _native("Onboard Diff Power Increase"),
        "diff_power_decrease": _native("Onboard Diff Power Decrease"),
        "diff_coast_increase": _native("Onboard Diff Coast Increase"),
        "diff_coast_decrease": _native("Onboard Diff Coast Decrease"),
        "single_wipe": _native(
            "Wipers",
            status="related",
            note="The installed label does not establish a dedicated single-wipe behavior.",
        ),
    },
    "le_mans_ultimate": {
        "brake_migration_forward": _native("Brake Migration Forward"),
        "brake_migration_rearward": _native("Brake Migration Rearward"),
        "tc_2_increase": _native("Traction Control 2 Up"),
        "tc_2_decrease": _native("Traction Control 2 Down"),
        "tc_slip_angle_increase": _native("Traction Control Slip Angle Up"),
        "tc_slip_angle_decrease": _native("Traction Control Slip Angle Down"),
        "tc_override": _native("TCOverride"),
        "front_wing_increase": _native(
            "Front Flap",
            status="related",
            note="A single flap command does not establish separate increase/decrease behavior.",
        ),
        "front_wing_decrease": _native(
            "Front Flap",
            status="related",
            note="A single flap command does not establish separate increase/decrease behavior.",
        ),
        "rear_wing_increase": _native(
            "Rear Flap",
            status="related",
            note="Rear Flap is also the installed DRS command, not a proven setup increment.",
        ),
        "rear_wing_decrease": _native(
            "Rear Flap",
            status="related",
            note="Rear Flap is also the installed DRS command, not a proven setup decrement.",
        ),
        "track_bar_increase": _native("Raise Track Bar"),
        "track_bar_decrease": _native("Lower Track Bar"),
        "single_wipe": _native(
            "Wipers",
            status="related",
            note="The installed label does not establish a dedicated single-wipe behavior.",
        ),
        "skip_formation": _native("Skip Formation"),
        "ai_control_toggle": _native("Toggle AI Control"),
    },
}


TUNING_NATIVE_CONTROL_NAMES: dict[str, dict[str, NativeControlName]] = {
    game_id: {
        **{
            control_id: _missing(
                "not_observed" if game_id == "assetto_corsa_competizione" else "not_exposed",
                (
                    "No matching action was present in the inspected binding-dependent "
                    "controls.json."
                    if game_id == "assetto_corsa_competizione"
                    else "No matching identifier was found in the installed action vocabulary."
                ),
            )
            for control_id in TUNING_CONTROLS
        },
        **_TUNING_NATIVE_OVERRIDES[game_id],
    }
    for game_id in GAMES
}


_SYSTEM_NATIVE_OVERRIDES: dict[str, dict[str, NativeControlName]] = {
    "iracing": {
        "brake_misc_increase": _native("BrakeMiscInc"),
        "brake_misc_decrease": _native("BrakeMiscDec"),
        "tc_3_increase": _native("TractionControl3Inc"),
        "tc_3_decrease": _native("TractionControl3Dec"),
        "tc_4_increase": _native("TractionControl4Inc"),
        "tc_4_decrease": _native("TractionControl4Dec"),
        "shock_left_front_increase": _native("ShockLeftFrontInc"),
        "shock_left_front_decrease": _native("ShockLeftFrontDec"),
        "shock_right_front_increase": _native("ShockRightFrontInc"),
        "shock_right_front_decrease": _native("ShockRightFrontDec"),
        "shock_left_rear_increase": _native("ShockLeftRearInc"),
        "shock_left_rear_decrease": _native("ShockLeftRearDec"),
        "shock_right_rear_increase": _native("ShockRightRearInc"),
        "shock_right_rear_decrease": _native("ShockRightRearDec"),
        "mguk_fixed_deployment_increase": _native("MGUKDeployFixedInc"),
        "mguk_fixed_deployment_decrease": _native("MGUKDeployFixedDec"),
        "rf_brake_attachment_toggle": _native("RFBrakeAttachedToggle"),
        "fuel_no_cut_toggle": _native("FuelNoCutToggle"),
        "hybrid_boost_hold": _native("HysBoostHold"),
        "hybrid_regen_hold": _native("HysRegenHold"),
        "hybrid_no_boost_toggle": _native("HysNoBoostToggle"),
        "text_chat": _native("TChatInitiate"),
        "voice_channel_next": _native("VChatChannelNext"),
        "voice_channel_previous": _native("VChatChannelPrev"),
        "voice_mute": _native("VChatMute"),
        "spotter_mute": _native(
            "SPCCShutUp",
            status="related",
            note="Shut Up is a temporary spotter-silence command, not necessarily a mute toggle.",
        ),
        "ffb_auto_adjust": _native("AutoFFB"),
    },
    "assetto_corsa": {},
    "assetto_corsa_competizione": {},
    "assetto_corsa_evo": {
        "front_bump_damper_increase": _native(
            "231: InputAction_Car_Front_Bump_Damper_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "front_bump_damper_decrease": _native(
            "231: InputAction_Car_Front_Bump_Damper_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "front_rebound_damper_increase": _native(
            "232: InputAction_Car_Front_Rebound_Damper_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "front_rebound_damper_decrease": _native(
            "232: InputAction_Car_Front_Rebound_Damper_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "rear_bump_damper_increase": _native(
            "233: InputAction_Car_Rear_Bump_Damper_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "rear_bump_damper_decrease": _native(
            "233: InputAction_Car_Rear_Bump_Damper_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "rear_rebound_damper_increase": _native(
            "234: InputAction_Car_Rear_Rebound_Damper_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "rear_rebound_damper_decrease": _native(
            "234: InputAction_Car_Rear_Rebound_Damper_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "ers_heat_charging_toggle": _native("1702: InputAction_Car_Ers_Heat_Charging_Toggle"),
        "map_open": _native("524: InputAction_UI_OpenMap"),
    },
    "automobilista_2": {
        "active_suspension_damping_increase": _native("ActiveSusp Damping Increase"),
        "active_suspension_damping_decrease": _native("ActiveSusp Damping Decrease"),
        "active_suspension_reaction_increase": _native(
            "ActiveSusp Reaction Speed Increase"
        ),
        "active_suspension_reaction_decrease": _native(
            "ActiveSusp Reaction Speed Decrease"
        ),
        "seat_angle_up": _native("Seat Angle Up"),
        "seat_angle_down": _native("Seat Angle Down"),
        "seat_reset": _native("Reset Seat Position"),
        "driver_list": _native("Driver List"),
        "lap_info_cycle": _native("Cycle Lap Info"),
        "radio_station_next": _native("Next Radio Station"),
        "text_chat": _native("Realtime Chat"),
    },
    "le_mans_ultimate": {
        "track_map_cycle": _native("Driver Overlay Cycle Track Map"),
        "vehicle_status": _native("Vehicle Status"),
        "text_chat": _native("Realtime Chat"),
        "ffb_reset": _native("Reset Force Feedback"),
    },
}


SYSTEM_NATIVE_CONTROL_NAMES: dict[str, dict[str, NativeControlName]] = {
    game_id: {
        **{
            control_id: _missing(
                "not_observed" if game_id == "assetto_corsa_competizione" else "not_exposed",
                (
                    "No matching action was present in the inspected binding-dependent "
                    "controls.json."
                    if game_id == "assetto_corsa_competizione"
                    else "No matching identifier was found in the installed action vocabulary."
                ),
            )
            for control_id in SYSTEM_CONTROLS
        },
        **_SYSTEM_NATIVE_OVERRIDES[game_id],
    }
    for game_id in GAMES
}


_UTILITY_NATIVE_OVERRIDES: dict[str, dict[str, NativeControlName]] = {
    "iracing": {
        **{f"gear_{number}": _native(f"Gear{number}") for number in range(10, 17)},
        "telltale_reset": _native("TellTaleReset"),
        "hand_warning": _native("HandUpWarning"),
        "dash_page_2_next": _native("DashPage2Inc"),
        "dash_page_2_previous": _native("DashPage2Dec"),
        "pit_summary_toggle": _native("PitSummaryToggle"),
        "driving_line_toggle": _native("ToggleDrivingLine"),
        "speed_gear_display_toggle": _native("ToggleSpeedGearDisplay"),
        "radio_display_toggle": _native("ToggleRadioDisplay"),
        "ui_scale_increase": _native("ScaleUIUp"),
        "ui_scale_decrease": _native("ScaleUIDown"),
        "look_up": _native("LookUp"),
        "look_down": _native("LookDown"),
        **{
            f"quick_chat_{number}": _native(f"AutoChat{number}")
            for number in range(1, 16)
        },
        "voice_driver_mute": _native("VChatDriverMute"),
        "voice_volume_increase": _native("VChatVolumeUp"),
        "voice_volume_decrease": _native("VChatVolumeDown"),
        "spotter_volume_increase": _native("SPCCVolumeUp"),
        "spotter_volume_decrease": _native("SPCCVolumeDown"),
        "spotter_lap_times_toggle": _native("SPCCToggleLapTimes"),
        "spotter_damage_report": _native("SPCCDamageReport"),
        "spotter_weather_report": _native("SPCCWeatherReport"),
        "master_volume_increase": _native("MasterVolumeUp"),
        "master_volume_decrease": _native("MasterVolumeDown"),
        "lfe_volume_increase": _native("LFEVolumeUp"),
        "lfe_volume_decrease": _native("LFEVolumeDown"),
        "trueforce_volume_increase": _native("TrueForceVolumeUp"),
        "trueforce_volume_decrease": _native("TrueForceVolumeDown"),
        "text_chat_reply": _native("TChatReply"),
        "text_chat_toggle": _native("TChatToggle"),
    },
    "assetto_corsa": {
        "mguh_mode": _native("[MGUH_MODE]"),
        "optional_vehicle_animation": _native(
            "[ACTION_CELEBRATE]",
            "[ACTION_CLAIM]",
            status="related",
            note="These are two specific driver animations, not a generic animation selector.",
        ),
    },
    "assetto_corsa_competizione": {
        "ui_up": _native("Up"),
        "ui_down": _native("Down"),
        "ui_left": _native("Left"),
        "ui_right": _native("Right"),
        "ui_confirm": _native(
            "Forward",
            status="related",
            note="The inspected code is Forward; confirm semantics need in-game validation.",
        ),
        "ui_cancel": _native(
            "Backward",
            status="related",
            note="The inspected code is Backward; cancel semantics need in-game validation.",
        ),
        "ui_page_up": _native(
            "CycleLeft",
            status="related",
            note="CycleLeft is related to page navigation but is not named Page Up.",
        ),
        "ui_page_down": _native(
            "CycleRight",
            status="related",
            note="CycleRight is related to page navigation but is not named Page Down.",
        ),
    },
    "assetto_corsa_evo": {
        "ui_up": _native("510: InputAction_UI_Up"),
        "ui_down": _native("511: InputAction_UI_Down"),
        "ui_left": _native("512: InputAction_UI_Left"),
        "ui_right": _native("513: InputAction_UI_Right"),
        "ui_confirm": _native("516: InputAction_UI_Confirm"),
        "ui_cancel": _native("517: InputAction_UI_Cancel"),
        "ui_menu": _native("518: InputAction_UI_Menu"),
        "ui_page_up": _native("514: InputAction_UI_PageUp"),
        "ui_page_down": _native("515: InputAction_UI_PageDown"),
        "mirrors_cycle": _native(
            "161: InputAction_Car_Mirrors_Cycle_X_2",
            status="compound",
            note="Packed two-way mirror-cycle action; direction encoding is not decoded.",
        ),
        "mirror_pitch_up": _native(
            "162: InputAction_Car_Mirrors_Pitch_X_2",
            status="compound",
            note="Packed two-way action; up/down encoding is not decoded.",
        ),
        "mirror_pitch_down": _native(
            "162: InputAction_Car_Mirrors_Pitch_X_2",
            status="compound",
            note="Packed two-way action; up/down encoding is not decoded.",
        ),
        "mirror_yaw_left": _native(
            "163: InputAction_Car_Mirrors_Yaw_X_2",
            status="compound",
            note="Packed two-way action; left/right encoding is not decoded.",
        ),
        "mirror_yaw_right": _native(
            "163: InputAction_Car_Mirrors_Yaw_X_2",
            status="compound",
            note="Packed two-way action; left/right encoding is not decoded.",
        ),
        "mirror_fov_increase": _native(
            "164: InputAction_Car_Mirrors_Fov_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "mirror_fov_decrease": _native(
            "164: InputAction_Car_Mirrors_Fov_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "h_shifter_toggle": _native("299: InputAction_Car_H_Shifter_Toggle"),
        "retractable_headlights_toggle": _native(
            "135: InputAction_Car_Retractable_HeadLights_Toggle"
        ),
        "esc_increase": _native(
            "149: InputAction_Car_ESC_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "esc_decrease": _native(
            "149: InputAction_Car_ESC_Cycle_X_2",
            status="compound",
            note="Packed two-way action; increase/decrease encoding is not decoded.",
        ),
        "show_points_of_interest": _native("523: InputAction_UI_ShowPoi"),
        "optional_vehicle_animation": _native(
            "913: InputAction_Car_Optional_Animation_X_5",
            status="compound",
            note="Packed five-way optional-animation action; sub-action encoding is not decoded.",
        ),
    },
    "automobilista_2": {
        "stability_control_toggle": _native("Toggle Stability Control"),
        "auto_clutch_toggle": _native("Toggle Auto Clutch"),
        "auto_gears_toggle": _native("Toggle Auto Gears"),
        "auto_brake_toggle": _native("Toggle Auto Brake"),
        "auto_steer_toggle": _native("Toggle Auto Steer"),
        "tc_force_on": _native("Traction Control On"),
        "tc_force_off": _native("Traction Control Off"),
        "nitrous": _native("Nitrous"),
        "look_up": _native("Look Up"),
        "look_down": _native("Look Down"),
        "ffb_tone_increase": _native("Increase Force Feedback Tone"),
        "ffb_tone_decrease": _native("Decrease Force Feedback Tone"),
        "auto_shift_mode_increase": _native("Onboard Auto Shift Mode Increase"),
        "auto_shift_mode_decrease": _native("Onboard Auto Shift Mode Decrease"),
        "in_car_menu_toggle": _native("ICM"),
    },
    "le_mans_ultimate": {
        **{
            f"quick_chat_{number}": _native(f"Quick Chat #{number}")
            for number in (*range(1, 10), 12)
        },
        "cursor_toggle": _native("Toggle Cursor"),
        "alternate_escape": _native("Alternate Esc"),
        "restart_race": _native("Restart Race"),
        "triples_toggle": _native("Triples"),
    },
}


UTILITY_NATIVE_CONTROL_NAMES: dict[str, dict[str, NativeControlName]] = {
    game_id: {
        **{
            control_id: _missing(
                "not_observed" if game_id == "assetto_corsa_competizione" else "not_exposed",
                (
                    "No matching action was present in the inspected binding-dependent "
                    "controls.json."
                    if game_id == "assetto_corsa_competizione"
                    else "No matching identifier was found in the installed action vocabulary."
                ),
            )
            for control_id in UTILITY_CONTROLS
        },
        **_UTILITY_NATIVE_OVERRIDES[game_id],
    }
    for game_id in GAMES
}


_EXTENDED_NATIVE_OVERRIDES: dict[str, dict[str, NativeControlName]] = {
    "iracing": {
        "abs_position": _native("ABSLevel"),
        "front_arb_position": _native("AntiRollFrontLevel"),
        "rear_arb_position": _native("AntiRollRearLevel"),
        "turbo_boost_position": _native("BoostLevelLevel"),
        "brake_bias_position": _native("BrakeBiasLevel"),
        "brake_bias_fine_position": _native("BrakeBiasFineLevel"),
        "brake_misc_position": _native("BrakeMiscLevel"),
        "peak_brake_bias_position": _native("PeakBrakeBiasLevel"),
        "dash_page_position": _native("DashPageLevel"),
        "dash_page_2_position": _native("DashPage2Level"),
        "diff_preload_position": _native("DiffPreloadLevel"),
        "diff_entry_position": _native("DiffEntryLevel"),
        "diff_middle_position": _native("DiffMiddleLevel"),
        "diff_exit_position": _native("DiffExitLevel"),
        "engine_braking_position": _native("EngineBrakingLevel"),
        "engine_power_position": _native("EnginePowerLevel"),
        "fuel_cut_position": _native("FuelCutPositionLevel"),
        "fuel_mixture_position": _native("FuelMixtureLevel"),
        "launch_rpm_position": _native("LaunchRPMLevel"),
        "mguk_fixed_deployment_position": _native("MGUKDeployFixedLevel"),
        "mguk_deployment_mode_position": _native("MGUKDeployModeLevel"),
        "mguk_regen_position": _native("MGUKRegenGainLevel"),
        "power_steering_position": _native("PowerSteeringLevel"),
        "qualifying_tape_position": _native("QTapeLevel"),
        "shock_left_front_position": _native("ShockLeftFrontLevel"),
        "shock_right_front_position": _native("ShockRightFrontLevel"),
        "shock_left_rear_position": _native("ShockLeftRearLevel"),
        "shock_right_rear_position": _native("ShockRightRearLevel"),
        "throttle_shape_position": _native("ThrottleShapeLevel"),
        "tc_position": _native("TractionControlLevel"),
        "tc_2_position": _native("TractionControl2Level"),
        "tc_3_position": _native("TractionControl3Level"),
        "tc_4_position": _native("TractionControl4Level"),
        "weight_jacker_left_position": _native("WeightJackerLeftLevel"),
        "weight_jacker_right_position": _native("WeightJackerRightLevel"),
        "front_wing_position": _native("WingFrontLevel"),
        "rear_wing_position": _native("WingRearLevel"),
        **{
            f"black_box_{number}": _native(f"BlackBoxF{number}")
            for number in range(1, 13)
        },
        "black_box_size": _native("BlackBoxSize"),
        "black_box_toggle": _native("BlackBoxToggle"),
        "custom_sector_start": _native("CustSectSetStart"),
        "custom_sector_end": _native("CustSectSetEnd"),
        "driver_horizon_increase": _native("DCamVanishYInc"),
        "driver_horizon_decrease": _native("DCamVanishYDec"),
        "dash_box_toggle": _native("DashBoxToggle"),
        "driver_marker": _native("IrsdkDriverMarker"),
        "previous_camera": _native("PrevDrivingCam"),
        "qualifying_tape_increase": _native("QTapeInc"),
        "qualifying_tape_decrease": _native("QTapeDec"),
        "recenter_tilt_axis": _native("RecenterTiltAxis"),
        "reload_car_texture": _native("ReloadCarTexture"),
        "latency_report": _native("ReportLatency"),
        "active_reset_save": _native("SaveActiveReset"),
        "active_reset_run": _native("RunActiveReset"),
        "spotter_leader_line": _native("SPCCAnounceLeaderLine"),
        "splits_delta_next": _native("SplitsDeltaNext"),
        "splits_delta_previous": _native("SplitsDeltaPrev"),
        "layout_edit_toggle": _native("ToggleEditLayoutMode"),
        "radar_toggle": _native("ToggleRadar"),
        "reference_car_toggle": _native("ToggleRefCar"),
        "system_meter_toggle": _native("ToggleSystemMeterDisplay"),
        "interface_visibility_toggle": _native("ToggleUIVisible"),
        "video_capture_toggle": _native("ToggleVideoCapture"),
        "video_timer_toggle": _native("ToggleVideoTimerDisplay"),
        "sdk_logging_toggle": _native("ToggleirsdkDiskLogging"),
        "giant_screenshot": _native("TriggerGiantScreenshotCapture"),
        "camera_zoom_in": _native(
            "CamFOVDec", note="Decreasing camera FOV corresponds to zooming in."
        ),
        "camera_zoom_out": _native(
            "CamFOVInc", note="Increasing camera FOV corresponds to zooming out."
        ),
    },
    "assetto_corsa": {},
    "assetto_corsa_competizione": {},
    "assetto_corsa_evo": {
        "abs_position": _native("145: InputAction_Car_ABS_Direct_X_15"),
        "dash_page_position": _native("126: InputAction_Car_Display_Page_Direct_X_5"),
        "engine_power_position": _native(
            "166: InputAction_Car_PerformanceMode_Direct_X_10",
            status="related",
            note="Performance mode can affect more than engine power.",
        ),
        "tc_position": _native("141: InputAction_Car_TractionControl_Direct_X_15"),
        "headlight_stage_direct": _native("122: InputAction_Car_Light_Direct_X_3"),
        "display_device_direct": _native(
            "124: InputAction_Car_Display_Device_Direct_X_5"
        ),
        "tc_cut_position": _native("143: InputAction_Car_TractionControl_Cut_Direct_X_15"),
        "engine_map_position": _native("147: InputAction_Car_Engine_Map_Direct_X_10"),
        "stability_control_position": _native("150: InputAction_Car_ESC_Direct_X_10"),
        "wiper_stage_direct": _native("156: InputAction_Car_Wipers_Direct_X_5"),
        "electronic_brake_balance_increase": _native(
            "235: InputAction_Car_Ebb_Cycle_X_2",
            status="compound",
            note="Packed two-way EBB action; increase/decrease encoding is not decoded.",
        ),
        "electronic_brake_balance_decrease": _native(
            "235: InputAction_Car_Ebb_Cycle_X_2",
            status="compound",
            note="Packed two-way EBB action; increase/decrease encoding is not decoded.",
        ),
        "vr_panel_forward": _native("531: InputAction_UI_Vr_Panel_Forward"),
        "vr_panel_backward": _native("532: InputAction_UI_Vr_Panel_Backward"),
        "vr_panel_scale_increase": _native("533: InputAction_UI_Vr_Panel_ScaleUp"),
        "vr_panel_scale_decrease": _native("534: InputAction_UI_Vr_Panel_ScaleDown"),
        "driving_camera_mode": _native("400: InputAction_Camera_Drivable"),
        "onboard_camera_mode": _native("406: InputAction_Camera_Onboard"),
        "spectator_camera_mode": _native(
            "404: InputAction_Camera_Helicopter",
            status="related",
            note="Helicopter is one spectator-style camera, not the entire spectator group.",
        ),
        "tracking_camera_mode": _native("403: InputAction_Camera_Track"),
    },
    "automobilista_2": {
        "previous_camera": _native("Cycle Cam Back"),
        "camera_view_set": _native("Change View Set"),
    },
    "le_mans_ultimate": {
        "cpu_time_display": _native("CPU Time"),
        "framerate_display": _native("Framerate"),
        "camera_zoom_in": _native("Camera Zoom In"),
        "camera_zoom_out": _native("Camera Zoom Out"),
        "driving_camera_mode": _native("Driving Cameras"),
        "onboard_camera_mode": _native("Onboard Cameras"),
        "spectator_camera_mode": _native("Spectator Cameras"),
        "swingman_camera_mode": _native("Swingman Camera"),
        "tracking_camera_mode": _native("Tracking Cameras"),
        "original_vehicle_view": _native("View Original Vehicle"),
        "instant_replay": _native("Instant Replay"),
        "swingman_up": _native("Swingman Up"),
        "swingman_down": _native("Swingman Down"),
        "swingman_left": _native("Swingman Left"),
        "swingman_right": _native("Swingman Right"),
        "swingman_reset": _native("Swingman Reset"),
        "swingman_zoom_in": _native("Swingman Zoom In"),
        "swingman_zoom_out": _native("Swingman Zoom Out"),
    },
}


EXTENDED_NATIVE_CONTROL_NAMES: dict[str, dict[str, NativeControlName]] = {
    game_id: {
        **{
            control_id: _missing(
                "not_observed" if game_id == "assetto_corsa_competizione" else "not_exposed",
                (
                    "No matching action was present in the inspected binding-dependent "
                    "controls.json."
                    if game_id == "assetto_corsa_competizione"
                    else "No matching identifier was found in the installed action vocabulary."
                ),
            )
            for control_id in EXTENDED_CONTROLS
        },
        **_EXTENDED_NATIVE_OVERRIDES[game_id],
    }
    for game_id in GAMES
}


_CAMERA_NATIVE_OVERRIDES: dict[str, dict[str, NativeControlName]] = {
    "iracing": {
        "camera_altitude_increase": _native(
            "CamAltInc", status="related", note="Positive camera-axis direction needs validation."
        ),
        "camera_altitude_decrease": _native(
            "CamAltDec", status="related", note="Negative camera-axis direction needs validation."
        ),
        "camera_lateral_increase": _native(
            "CamLatInc", status="related", note="Positive camera-axis direction needs validation."
        ),
        "camera_lateral_decrease": _native(
            "CamLatDec", status="related", note="Negative camera-axis direction needs validation."
        ),
        "camera_longitudinal_increase": _native(
            "CamLongInc", status="related", note="Positive camera-axis direction needs validation."
        ),
        "camera_longitudinal_decrease": _native(
            "CamLongDec", status="related", note="Negative camera-axis direction needs validation."
        ),
        "camera_yaw_increase": _native(
            "CamYawInc", status="related", note="Positive camera-axis direction needs validation."
        ),
        "camera_yaw_decrease": _native(
            "CamYawDec", status="related", note="Negative camera-axis direction needs validation."
        ),
        "camera_pitch_increase": _native(
            "CamPitchInc", status="related", note="Positive camera-axis direction needs validation."
        ),
        "camera_pitch_decrease": _native(
            "CamPitchDec", status="related", note="Negative camera-axis direction needs validation."
        ),
        "camera_roll_increase": _native(
            "CamRollInc", status="related", note="Positive camera-axis direction needs validation."
        ),
        "camera_roll_decrease": _native(
            "CamRollDec", status="related", note="Negative camera-axis direction needs validation."
        ),
        "camera_zoom_toggle": _native("CamToggleZoom"),
        "focus_next_car": _native("FocusNextCar"),
        "focus_previous_car": _native("FocusPrevCar"),
        "focus_player_car": _native("FocusPlayerCar"),
    },
    "assetto_corsa": {},
    "assetto_corsa_competizione": {},
    "assetto_corsa_evo": {
        "camera_altitude_increase": _native("410: InputAction_Camera_PanUp"),
        "camera_altitude_decrease": _native("411: InputAction_Camera_PanDown"),
        "camera_lateral_decrease": _native("412: InputAction_Camera_PanLeft"),
        "camera_lateral_increase": _native("413: InputAction_Camera_PanRight"),
        "camera_longitudinal_increase": _native("414: InputAction_Camera_Forward"),
        "camera_longitudinal_decrease": _native("415: InputAction_Camera_Backward"),
        "camera_yaw_decrease": _native("416: InputAction_Camera_YawLeft"),
        "camera_yaw_increase": _native("417: InputAction_Camera_YawRight"),
        "camera_pitch_increase": _native("420: InputAction_Camera_PitchUp"),
        "camera_pitch_decrease": _native("421: InputAction_Camera_PitchDown"),
        "camera_roll_increase": _native("422: InputAction_Camera_RollRight"),
        "camera_roll_decrease": _native("423: InputAction_Camera_RollLeft"),
        "camera_pan_up_slow": _native("1410: InputAction_Camera_PanUp_Slow"),
        "camera_pan_down_slow": _native("1411: InputAction_Camera_PanDown_Slow"),
        "camera_pan_left_slow": _native("1412: InputAction_Camera_PanLeft_Slow"),
        "camera_pan_right_slow": _native("1413: InputAction_Camera_PanRight_Slow"),
        "camera_forward_slow": _native("1414: InputAction_Camera_Forward_Slow"),
        "camera_backward_slow": _native("1415: InputAction_Camera_Backward_Slow"),
        "camera_yaw_left_slow": _native("1416: InputAction_Camera_YawLeft_Slow"),
        "camera_yaw_right_slow": _native("1417: InputAction_Camera_YawRight_Slow"),
        "camera_pitch_up_slow": _native("1420: InputAction_Camera_PitchUp_Slow"),
        "camera_pitch_down_slow": _native("1421: InputAction_Camera_PitchDown_Slow"),
        "camera_roll_right_slow": _native("1422: InputAction_Camera_RollRight_Slow"),
        "camera_roll_left_slow": _native("1423: InputAction_Camera_RollLeft_Slow"),
        "camera_pan_up_fast": _native("2410: InputAction_Camera_PanUp_Fast"),
        "camera_pan_down_fast": _native("2411: InputAction_Camera_PanDown_Fast"),
        "camera_pan_left_fast": _native("2412: InputAction_Camera_PanLeft_Fast"),
        "camera_pan_right_fast": _native("2413: InputAction_Camera_PanRight_Fast"),
        "camera_forward_fast": _native("2414: InputAction_Camera_Forward_Fast"),
        "camera_backward_fast": _native("2415: InputAction_Camera_Backward_Fast"),
        "camera_yaw_left_fast": _native("2416: InputAction_Camera_YawLeft_Fast"),
        "camera_yaw_right_fast": _native("2417: InputAction_Camera_YawRight_Fast"),
        "camera_pitch_up_fast": _native("2420: InputAction_Camera_PitchUp_Fast"),
        "camera_pitch_down_fast": _native("2421: InputAction_Camera_PitchDown_Fast"),
        "camera_roll_right_fast": _native("2422: InputAction_Camera_RollRight_Fast"),
        "camera_roll_left_fast": _native("2423: InputAction_Camera_RollLeft_Fast"),
        "drone_camera_toggle": _native("0: InputAction_Camera_Drone_Toggle"),
        "onboard_free_camera": _native("401: InputAction_Camera_OnBoardFree"),
        "free_camera": _native("402: InputAction_Camera_Free"),
        "camera_view_reset": _native("418: InputAction_Camera_ResetView"),
        "camera_view_reset_cancel": _native("419: InputAction_Camera_CancelResetView"),
        "camera_zoom_toggle": _native("424: InputAction_Camera_Zoom_Toggle"),
        "showroom_rotate_car": _native("430: InputAction_Camera_Showroom_RotateCar"),
        "showroom_internal_view": _native("431: InputAction_Camera_Showroom_InternalView"),
        "focus_next_car": _native("501: InputAction_Camera_Select_Next_Car"),
        "focus_previous_car": _native("502: InputAction_Camera_Select_Prev_Car"),
        "focus_player_car": _native("503: InputAction_Camera_Select_Player_Car"),
    },
    "automobilista_2": {},
    "le_mans_ultimate": {},
}


CAMERA_NATIVE_CONTROL_NAMES: dict[str, dict[str, NativeControlName]] = {
    game_id: {
        **{
            control_id: _missing(
                "not_observed" if game_id == "assetto_corsa_competizione" else "not_exposed",
                (
                    "No matching action was present in the inspected binding-dependent "
                    "controls.json."
                    if game_id == "assetto_corsa_competizione"
                    else "No matching identifier was found in the installed action vocabulary."
                ),
            )
            for control_id in CAMERA_CONTROLS
        },
        **_CAMERA_NATIVE_OVERRIDES[game_id],
    }
    for game_id in GAMES
}


_MEDIA_NATIVE_OVERRIDES: dict[str, dict[str, NativeControlName]] = {
    "iracing": {
        "camera_acquire_start": _native("CamAcquireStart"),
        "camera_acquire_end": _native("CamAcquireEnd"),
        "camera_copy": _native("CamCopy"),
        "camera_exposure_increase": _native("CamExposureInc"),
        "camera_exposure_decrease": _native("CamExposureDec"),
        "camera_f_number_increase": _native("CamFNumberInc"),
        "camera_f_number_decrease": _native("CamFNumberDec"),
        "camera_focus_depth_increase": _native("CamFocusDepthInc"),
        "camera_focus_depth_decrease": _native("CamFocusDepthDec"),
        "camera_ir_max_temperature_increase": _native("CamIRMaxTempInc"),
        "camera_ir_max_temperature_decrease": _native("CamIRMaxTempDec"),
        "camera_ir_min_temperature_increase": _native("CamIRMinTempInc"),
        "camera_ir_min_temperature_decrease": _native("CamIRMinTempDec"),
        "camera_insert": _native("CamInsert"),
        "camera_listener_gain_auto": _native("CamListenerGainBiasAuto"),
        "camera_listener_gain_increase": _native("CamListenerGainBiasInc"),
        "camera_listener_gain_decrease": _native("CamListenerGainBiasDec"),
        "camera_load_car": _native("CamLoadCar"),
        "camera_load_track": _native("CamLoadTrack"),
        "camera_move_multiplier_increase": _native("CamMoveMultInc"),
        "camera_move_multiplier_decrease": _native("CamMoveMultDec"),
        "camera_near_plane_increase": _native("CamNearPlaneBiasInc"),
        "camera_near_plane_decrease": _native("CamNearPlaneBiasDec"),
        "camera_paste": _native("CamPaste"),
        "camera_radius_increase": _native("CamRadInc"),
        "camera_radius_decrease": _native("CamRadDec"),
        "camera_remove": _native("CamRemove"),
        "camera_save_car": _native("CamSaveCar"),
        "camera_save_track": _native("CamSaveTrack"),
        "camera_shake_increase": _native("CamShakePctInc"),
        "camera_shake_decrease": _native("CamShakePctDec"),
        "camera_acquire_toggle": _native("CamToggleAcquire"),
        "camera_aim_type_toggle": _native("CamToggleAimType"),
        "camera_beyond_fence_toggle": _native("CamToggleBeyondFence"),
        "camera_control_active_toggle": _native("CamToggleCamCtrlActive"),
        "camera_local_copy_toggle": _native("CamToggleCamLocalCopy"),
        "camera_tool_toggle": _native("CamToggleCamTool"),
        "camera_display_toggle": _native("CamToggleDisplay"),
        "camera_focus_toggle": _native("CamToggleFocus"),
        "camera_weight_toggle": _native("CamToggleHasWeight"),
        "camera_in_cockpit_toggle": _native("CamToggleInCockpit"),
        "camera_infrared_toggle": _native("CamToggleIsIR"),
        "camera_move_acceleration_toggle": _native("CamToggleMoveMultAccel"),
        "camera_move_scale_toggle": _native("CamToggleMoveMultScale"),
        "camera_parabolic_microphone_toggle": _native("CamToggleParabolicMic"),
        "camera_pitch_gyro_toggle": _native("CamTogglePitchGyro"),
        "camera_position_type_toggle": _native("CamTogglePosType"),
        "camera_roll_gyro_toggle": _native("CamToggleRollGyro"),
        "camera_sensor_type_toggle": _native("CamToggleSensorType"),
        "camera_shot_queue_toggle": _native("CamToggleUseShotQ"),
        "camera_vanishing_point_x_increase": _native("CamVanishXInc"),
        "camera_vanishing_point_x_decrease": _native("CamVanishXDec"),
        "camera_vanishing_point_y_increase": _native("CamVanishYInc"),
        "camera_vanishing_point_y_decrease": _native("CamVanishYDec"),
        "camera_velocity_increase": _native("CamVelInc"),
        "camera_velocity_decrease": _native("CamVelDec"),
        "camera_group_copy": _native("GroupCopy"),
        "camera_group_paste": _native("GroupPaste"),
        "replay_next_camera": _native("NextRpyCamCam"),
        "replay_previous_camera": _native("PrevRpyCamCam"),
        "replay_next_camera_group": _native("NextRpyCamGroup"),
        "replay_previous_camera_group": _native("PrevRpyCamGroup"),
        "replay_fast_forward": _native("RpyFF"),
        "replay_frame_advance": _native("RpyFrameAdv"),
        "replay_frame_rewind": _native("RpyFrameRew"),
        "replay_next_incident": _native("RpyIncidentFF"),
        "replay_previous_incident": _native("RpyIncidentRew"),
        "replay_rate_increase": _native("RpyIncreaseRate"),
        "replay_next_lap": _native("RpyLapFF"),
        "replay_previous_lap": _native("RpyLapRew"),
        "replay_pause_play": _native("RpyPausePlay"),
        "replay_rewind": _native("RpyRew"),
        "replay_next_session": _native("RpySessionFF"),
        "replay_previous_session": _native("RpySessionRew"),
        "replay_stop": _native("RpyStop"),
        "replay_to_end": _native("RpyToEnd"),
        "replay_to_start": _native("RpyToStart"),
    },
    "assetto_corsa": {},
    "assetto_corsa_competizione": {},
    "assetto_corsa_evo": {},
    "automobilista_2": {},
    "le_mans_ultimate": {},
}


MEDIA_NATIVE_CONTROL_NAMES: dict[str, dict[str, NativeControlName]] = {
    game_id: {
        **{
            control_id: _missing(
                "not_observed" if game_id == "assetto_corsa_competizione" else "not_exposed",
                (
                    "No matching action was present in the inspected binding-dependent "
                    "controls.json."
                    if game_id == "assetto_corsa_competizione"
                    else "No matching identifier was found in the installed action vocabulary."
                ),
            )
            for control_id in MEDIA_CONTROLS
        },
        **_MEDIA_NATIVE_OVERRIDES[game_id],
    }
    for game_id in GAMES
}


NATIVE_CONTROL_NAMES = {
    game_id: {
        **BASIC_NATIVE_CONTROL_NAMES[game_id],
        **COMMON_NATIVE_CONTROL_NAMES[game_id],
        **ADVANCED_NATIVE_CONTROL_NAMES[game_id],
        **TUNING_NATIVE_CONTROL_NAMES[game_id],
        **SYSTEM_NATIVE_CONTROL_NAMES[game_id],
        **UTILITY_NATIVE_CONTROL_NAMES[game_id],
        **EXTENDED_NATIVE_CONTROL_NAMES[game_id],
        **CAMERA_NATIVE_CONTROL_NAMES[game_id],
        **MEDIA_NATIVE_CONTROL_NAMES[game_id],
    }
    for game_id in GAMES
}


def native_control_name(game_id: str, control_id: str) -> NativeControlName:
    """Return one complete crosswalk cell, raising ``KeyError`` for unknown IDs."""

    return NATIVE_CONTROL_NAMES[game_id][control_id]
