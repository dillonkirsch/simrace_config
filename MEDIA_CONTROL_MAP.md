# Advanced camera and replay control map

Batch 9 adds the final 77 user-facing controls found by the installed-game
inventory audit. These are iRacing's camera editor, camera-set persistence,
specialized camera options, and replay controls. No equivalent native action
was observed in the other five inventories, so those crosswalk cells are
recorded as `not_exposed` or `not_observed` rather than guessed.

## Camera editing and persistence

| Human-readable control | Central ID | iRacing name |
| --- | --- | --- |
| Start/end camera acquisition | `camera_acquire_start` / `camera_acquire_end` | `CamAcquireStart` / `CamAcquireEnd` |
| Copy/paste/insert/remove camera | `camera_copy` / `camera_paste` / `camera_insert` / `camera_remove` | `CamCopy` / `CamPaste` / `CamInsert` / `CamRemove` |
| Copy/paste camera group | `camera_group_copy` / `camera_group_paste` | `GroupCopy` / `GroupPaste` |
| Load/save car camera set | `camera_load_car` / `camera_save_car` | `CamLoadCar` / `CamSaveCar` |
| Load/save track camera set | `camera_load_track` / `camera_save_track` | `CamLoadTrack` / `CamSaveTrack` |
| Increase/decrease exposure | `camera_exposure_increase` / `camera_exposure_decrease` | `CamExposureInc` / `CamExposureDec` |
| Increase/decrease F-number | `camera_f_number_increase` / `camera_f_number_decrease` | `CamFNumberInc` / `CamFNumberDec` |
| Increase/decrease focus depth | `camera_focus_depth_increase` / `camera_focus_depth_decrease` | `CamFocusDepthInc` / `CamFocusDepthDec` |
| Increase/decrease infrared maximum temperature | `camera_ir_max_temperature_increase` / `camera_ir_max_temperature_decrease` | `CamIRMaxTempInc` / `CamIRMaxTempDec` |
| Increase/decrease infrared minimum temperature | `camera_ir_min_temperature_increase` / `camera_ir_min_temperature_decrease` | `CamIRMinTempInc` / `CamIRMinTempDec` |
| Auto/increase/decrease listener gain | `camera_listener_gain_auto` / `camera_listener_gain_increase` / `camera_listener_gain_decrease` | `CamListenerGainBiasAuto` / `CamListenerGainBiasInc` / `CamListenerGainBiasDec` |
| Increase/decrease movement multiplier | `camera_move_multiplier_increase` / `camera_move_multiplier_decrease` | `CamMoveMultInc` / `CamMoveMultDec` |
| Increase/decrease near-plane bias | `camera_near_plane_increase` / `camera_near_plane_decrease` | `CamNearPlaneBiasInc` / `CamNearPlaneBiasDec` |
| Increase/decrease radius | `camera_radius_increase` / `camera_radius_decrease` | `CamRadInc` / `CamRadDec` |
| Increase/decrease shake | `camera_shake_increase` / `camera_shake_decrease` | `CamShakePctInc` / `CamShakePctDec` |
| Increase/decrease velocity | `camera_velocity_increase` / `camera_velocity_decrease` | `CamVelInc` / `CamVelDec` |
| Move vanishing point right/left | `camera_vanishing_point_x_increase` / `camera_vanishing_point_x_decrease` | `CamVanishXInc` / `CamVanishXDec` |
| Move vanishing point up/down | `camera_vanishing_point_y_increase` / `camera_vanishing_point_y_decrease` | `CamVanishYInc` / `CamVanishYDec` |

## Specialized camera toggles

| Human-readable control | Central ID | iRacing name |
| --- | --- | --- |
| Toggle acquisition | `camera_acquire_toggle` | `CamToggleAcquire` |
| Cycle aim type | `camera_aim_type_toggle` | `CamToggleAimType` |
| Toggle beyond-fence permission | `camera_beyond_fence_toggle` | `CamToggleBeyondFence` |
| Toggle camera controls | `camera_control_active_toggle` | `CamToggleCamCtrlActive` |
| Toggle local copy | `camera_local_copy_toggle` | `CamToggleCamLocalCopy` |
| Toggle camera tool/display/focus | `camera_tool_toggle` / `camera_display_toggle` / `camera_focus_toggle` | `CamToggleCamTool` / `CamToggleDisplay` / `CamToggleFocus` |
| Toggle weighted movement | `camera_weight_toggle` | `CamToggleHasWeight` |
| Toggle in-cockpit state | `camera_in_cockpit_toggle` | `CamToggleInCockpit` |
| Toggle infrared mode | `camera_infrared_toggle` | `CamToggleIsIR` |
| Toggle movement acceleration/scaling | `camera_move_acceleration_toggle` / `camera_move_scale_toggle` | `CamToggleMoveMultAccel` / `CamToggleMoveMultScale` |
| Toggle parabolic microphone | `camera_parabolic_microphone_toggle` | `CamToggleParabolicMic` |
| Toggle pitch/roll gyro | `camera_pitch_gyro_toggle` / `camera_roll_gyro_toggle` | `CamTogglePitchGyro` / `CamToggleRollGyro` |
| Cycle position/sensor type | `camera_position_type_toggle` / `camera_sensor_type_toggle` | `CamTogglePosType` / `CamToggleSensorType` |
| Toggle shot queue | `camera_shot_queue_toggle` | `CamToggleUseShotQ` |

## Replay navigation and transport

| Human-readable control | Central ID | iRacing name |
| --- | --- | --- |
| Next/previous replay camera | `replay_next_camera` / `replay_previous_camera` | `NextRpyCamCam` / `PrevRpyCamCam` |
| Next/previous replay camera group | `replay_next_camera_group` / `replay_previous_camera_group` | `NextRpyCamGroup` / `PrevRpyCamGroup` |
| Fast-forward/rewind | `replay_fast_forward` / `replay_rewind` | `RpyFF` / `RpyRew` |
| Advance/rewind one frame | `replay_frame_advance` / `replay_frame_rewind` | `RpyFrameAdv` / `RpyFrameRew` |
| Next/previous incident | `replay_next_incident` / `replay_previous_incident` | `RpyIncidentFF` / `RpyIncidentRew` |
| Increase replay speed | `replay_rate_increase` | `RpyIncreaseRate` |
| Next/previous lap | `replay_next_lap` / `replay_previous_lap` | `RpyLapFF` / `RpyLapRew` |
| Pause/play | `replay_pause_play` | `RpyPausePlay` |
| Next/previous session | `replay_next_session` / `replay_previous_session` | `RpySessionFF` / `RpySessionRew` |
| Stop | `replay_stop` | `RpyStop` |
| Jump to end/start | `replay_to_end` / `replay_to_start` | `RpyToEnd` / `RpyToStart` |

This completes semantic evaluation of every user-facing native identifier in
the six-game inventory snapshot. The 124 raw unmatched strings left by the
audit are explicitly excluded metadata, developer/internal actions, or
showroom-only presentation actions.
