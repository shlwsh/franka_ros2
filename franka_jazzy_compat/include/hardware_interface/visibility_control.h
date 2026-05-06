// Copyright 2024 Open Source Robotics Foundation, Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef HARDWARE_INTERFACE__VISIBILITY_CONTROL_H_
#define HARDWARE_INTERFACE__VISIBILITY_CONTROL_H_

// This logic was borrowed from then namespaced Gazebo Math's
// visibility header
#if defined _WIN32 || defined __CYGWIN__
#define HARDWARE_INTERFACE_EXPORT __declspec(dllexport)
#define HARDWARE_INTERFACE_IMPORT __declspec(dllimport)
#elif __GNUC__ >= 4
#define HARDWARE_INTERFACE_EXPORT __attribute__((visibility("default")))
#define HARDWARE_INTERFACE_IMPORT __attribute__((visibility("hidden")))
#else
#define HARDWARE_INTERFACE_EXPORT
#define HARDWARE_INTERFACE_IMPORT
#endif

#ifndef HARDWARE_INTERFACE_EXPORT
#define HARDWARE_INTERFACE_EXPORT
#endif

#ifndef HARDWARE_INTERFACE_IMPORT
#define HARDWARE_INTERFACE_IMPORT
#endif

#ifdef __cplusplus
extern "C" {
#endif

// This will be used by library consumers only
#ifndef HARDWARE_INTERFACE_EXPORT
#ifdef HARDWARE_INTERFACE_IMPORT
// Building/using a shared library
#else
// Using a static library
#define HARDWARE_INTERFACE_EXPORT
#define HARDWARE_INTERFACE_IMPORT
#endif
#endif

#ifdef __cplusplus
}
#endif

#endif  // HARDWARE_INTERFACE__VISIBILITY_CONTROL_H_
