pub const Namespace = struct {
    parent: ?*Namespace,
    symbols: std.StringHashMap(EObject),
    templates: std.StringHashMap(componenttemplate.ComponentTemplate),
    allocator: Allocator,

    pub fn init(allocator: ?Allocator, parent: ?*Namespace) Namespace {
        const alloc = allocator orelse std.heap.page_allocator;
        return .{
            .parent = parent,
            .symbols = std.StringHashMap(EObject).init(alloc),
            .allocator = alloc,
            .templates = std.StringHashMap(componenttemplate.ComponentTemplate).init(alloc),
        };
    }

    pub fn define(self: *Namespace, name: []const u8, value: EObject) !void {
        try self.symbols.put(name, value);
    }

    pub fn lookup(self: *const Namespace, name: []const u8) ?EObject {
        if (self.symbols.get(name)) |val| return val;
        if (self.parent) |parent| return parent.lookup(name);
        return null;
    }
    pub fn addTemplate(self: *Namespace, name: []const u8, template: componenttemplate.ComponentTemplate) !void {
        try self.templates.put(name, template);
    }
    pub fn getTemplate(self: *const Namespace, name: []const u8) !?componenttemplate.ComponentTemplate {
        if (self.templates.get(name)) |val| return val;
        if (self.parent) |parent| return parent.getTemplate(name);
        return null;
    }
};

const std = @import("std");
const Allocator = std.mem.Allocator;

const objs = @import("objects.zig");
const EObject = objs.EObject;

const componenttemplate = @import("componenttemplate.zig");
