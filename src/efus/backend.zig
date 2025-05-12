pub const RendererBackend = struct {
    mount: *const fn (component: *Component) anyerror!void,
    update: *const fn (component: *Component) anyerror!void,
    unmount: *const fn (component: *Component) anyerror!void,
    init: *const fn (component: *Component, master: ?Component) anyerror!void,
};

pub const Mount = struct {
    widget: ?*anyopaque,
};

const objs = @import("objects.zig");
const Component = @import("component.zig").Component;
const std = @import("std");
