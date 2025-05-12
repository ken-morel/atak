fn test_mnt(c: *Component) anyerror!void {
    print("Mounting label\n", .{});
    for (c.children.items) |*child| {
        try child.mount();
    }
}
fn test_update(c: *Component) anyerror!void {
    print("updating Label\n", .{});
    for (c.children.items) |*child| {
        try child.update();
    }
}

fn test_unmount(c: *Component) anyerror!void {
    print("unmounting Label\n", .{});
    for (c.children.items) |*child| {
        try child.unmount();
    }
}

fn test_init(_: *Component, _: ?Component) anyerror!void {
    print("Initializing component with parent\n", .{});
}

const test_label_renderer = RendererBackend{
    .mount = test_mnt,
    .update = test_update,
    .unmount = test_unmount,
    .init = test_init,
};

const Label = ComponentTemplate{ // templates are defined in compile time
    .name = "Label",
    .parameters = EParameters{
        .parameters = &[_]EParameter{EParameter{
            .type = EType.String,
            .default = EObject.init(.{
                .String = "Default string",
            }),
            .name = "text",
        }},
    },
    .renderer = test_label_renderer,
};
pub fn main() !void {
    var parser = try efus.Parser.fromFile(null, "test.efus");
    var ctx = EvalContext.init(std.heap.page_allocator, Namespace.init(null, null));
    try ctx.namespace.addTemplate("Label", Label);
    if (try parser.parse()) |code| {
        const obj = try code.eval(ctx);
        print("Component {any}\n", .{obj});
        var comp = obj.?.value.Component;
        try comp.mount();
        try comp.update();
        try comp.unmount();
    }
}

const lib = @import("atak_lib");

const efus = @import("efus.zig");

const print = std.debug.print;
const std = @import("std");
const ComponentTemplate = @import("efus/componenttemplate.zig").ComponentTemplate;
const component = @import("efus/component.zig");
const Component = component.Component;
const attributemanager = @import("efus/attributemanager.zig");
const EParameters = attributemanager.EParameters;
const EParameter = attributemanager.EParameter;
const backend = @import("efus/backend.zig");
const RendererBackend = backend.RendererBackend;
const Mount = backend.Mount;
const errors = @import("efus/errors.zig");

const objs = @import("efus/objects.zig");
const EType = objs.EType;
const EObject = objs.EObject;

const namespace = @import("efus/namespace.zig");
const Namespace = namespace.Namespace;

const instruction = @import("efus/instruction.zig");
const EvalContext = instruction.EvalContext;
