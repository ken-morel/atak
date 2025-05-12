const std = @import("std");
const namespace = @import("namespace.zig");
const component = @import("component.zig");
const objects = @import("objects.zig");
const attributemanager = @import("attributemanager.zig");

const EObject = objects.EObject;
const ComponentTemplate = component.ComponentTemplate;
const EArguments = attributemanager.EArguments;
const Namespace = namespace.Namespace;
const EfusError = @import("errors.zig").EfusError;

pub const StackEntry = struct {
    instruction: Instruction,
    result: ?*component.Component,
};

pub const InstantiateComponentArgument = struct {
    key: []const u8,
    value: EObject,
};

pub const InstantiateComponent = struct {
    componentName: []const u8,
    componentAlias: ?[]const u8,
    arguments: std.ArrayList(InstantiateComponentArgument),
    allocator: std.mem.Allocator,
    indent: ?u32,

    pub fn init(
        allocator: std.mem.Allocator,
        name: []const u8,
        alias: ?[]const u8,
        args: ?std.ArrayList(InstantiateComponentArgument),
        indent: ?u32,
    ) InstantiateComponent {
        return .{
            .componentName = name,
            .componentAlias = alias,
            .arguments = args orelse std.ArrayList(InstantiateComponentArgument).init(allocator),
            .allocator = allocator,
            .indent = indent,
        };
    }

    fn _setIndent(self: *InstantiateComponent, indent: ?u32) void {
        self.indent = indent;
    }

    pub fn eval(self: *const InstantiateComponent, ctx: EvalContext) !?EObject {
        var parent_entry = findParentComponent(ctx.stack, self.indent);

        const template = try ctx.namespace.getTemplate(self.componentName) orelse return EfusError.TemplateNotFound;

        const comp = EObject.init(.{
            .Component = try template.instantiate(
                self.allocator,
                ctx.namespace,
                try EArguments.fromICArgs(self.allocator, self.arguments),
                if (parent_entry) |parent|
                    (if (parent.result) |result_ptr|
                        result_ptr.* // Dereference the pointer to get the Component
                    else
                        null)
                else
                    null,
            ),
        });
        if (parent_entry) |*parent| {
            if (parent.result) |pcomp| {
                try pcomp.addChild(comp.value.Component);
            }
        }
        return comp;
    }
};

pub const Instruction = union(enum) {
    InstantiateComponent: InstantiateComponent,
    DoNothing,

    pub fn setIndent(self: *Instruction, indent: u32) void {
        switch (self.*) {
            .InstantiateComponent => |*comp| comp._setIndent(indent),
            .DoNothing => {},
        }
    }

    pub fn getIndent(self: *const Instruction) ?u32 {
        return switch (self.*) {
            .InstantiateComponent => |comp| comp.indent,
            .DoNothing => null,
        };
    }

    pub fn eval(self: *Instruction, ctx: EvalContext) !?EObject {
        return switch (self.*) {
            .InstantiateComponent => |comp| comp.eval(ctx),
            .DoNothing => null,
        };
    }
};

fn findParentComponent(
    stack: std.ArrayList(StackEntry),
    current_indent: ?u32,
) ?StackEntry {
    var i = stack.items.len;
    while (i > 0) {
        i -= 1;
        const entry = stack.items[i];
        const entry_indent = entry.instruction.getIndent();

        if (entry_indent) |ei| {
            if (current_indent) |ci| {
                if (ei < ci) return entry;
            }
        }
    }
    return null;
}

pub const EvalContext = struct {
    allocator: std.mem.Allocator,
    namespace: Namespace,
    stack: std.ArrayList(StackEntry),

    pub fn init(allocator: std.mem.Allocator, names: Namespace) EvalContext {
        return .{
            .allocator = allocator,
            .namespace = names,
            .stack = std.ArrayList(StackEntry).init(allocator),
        };
    }

    pub fn pushInstruction(self: *EvalContext, instr: Instruction) !void {
        try self.stack.append(.{
            .instruction = instr,
            .result = null,
        });
    }
};
