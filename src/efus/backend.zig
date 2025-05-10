pub const RendererBackend = struct {
    mount: *const fn (component: *Component) anyerror!Mount,
    update: *const fn (component: *Component, mount: Mount) anyerror!void,
    unmount: ?*const fn (component: *Component, mount: Mount) void = null,
};

pub const Mount = struct {
    widget: *anyopaque,
};

const objs = @import("objects.zig");
const Component = @import("component.zig").Component;
const std = @import("std");
