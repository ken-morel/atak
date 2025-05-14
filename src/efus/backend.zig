pub const RendererBackend = struct {
    mount: *const fn (component: *Component) anyerror!void,
    update: *const fn (component: *Component) anyerror!void,
    unmount: *const fn (component: *Component) anyerror!void,
    init: *const fn (component: *Component, master: ?Component) anyerror!void,
    pub fn fromStruct(struc: type) RendererBackend {
        return .{
            .mount = struc.mount,
            .update = struc.update,
            .unmount = struc.unmount,
            .init = struc.init,
        };
    }
};

pub const Mount = struct {
    id: u32,
    pub fn zero() Mount {
        return .{
            .id = 0,
        };
    }
    pub fn next(self: *const Mount) Mount {
        return .{
            .id = self.id + 1,
        };
    }
    pub fn eq(self: *const Mount, other: Mount) bool {
        return self.id == other.id;
    }
};

const objs = @import("objects.zig");
const Component = @import("component.zig").Component;
const std = @import("std");
