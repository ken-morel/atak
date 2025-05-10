pub const Namespace = struct {
    parent: ?*Namespace, // Optional parent namespace (for scoping)
    symbols: std.StringHashMap(EObject),
    allocator: Allocator,

    pub fn init(allocator: Allocator, parent: ?*Namespace) Namespace {
        return .{
            .parent = parent,
            .symbols = std.StringHashMap(EObject).init(allocator),
            .allocator = allocator,
        };
    }

    pub fn set(self: *Namespace, name: []const u8, value: EObject) !void {
        try self.symbols.put(name, value);
    }

    pub fn get(self: *Namespace, name: []const u8) ?EObject {
        if (self.symbols.get(name)) |val| return val;
        if (self.parent) |parent| return parent.lookup(name);
        return null;
    }
};

const std = @import("std");
const Allocator = std.mem.Allocator;

const objs = @import("objects.zig");
const EObject = objs.EObject;
