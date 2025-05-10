pub const Component = struct {
    allocator: std.mem.Allocator,
    attributeManager: attributemanager.EAttributeManager,
    template: *componenttemplate.ComponentTemplate,
    namespace: *Namespace,
    _mount: ?backend.Mount = null,
    dirty: bool = false,

    pub fn mount(self: *Component) anyerror!backend.Mount {
        self._mount = try self.template.renderer.mount(self);
        return self._mount;
    }
    pub fn update(self: *Component) anyerror!void {
        try self.template.renderer.update(self, self._mount);
        self.dirty = false;
    }
    pub fn unmount(self: *Component) anyerror!void {
        try self.template.renderer.unmount(self, self._mount);
    }
};

const std = @import("std");
const componenttemplate = @import("componenttemplate.zig");
const attributemanager = @import("attributemanager.zig");
const backend = @import("backend.zig");
const Namespace = @import("namespace.zig").Namespace;
