fn test_mnt(_: *Component) !Mount {
    if (false) {
        return errors.EfusError;
    }
    return Mount{
        .widget = null,
    };
}

const test_label_renderer = RendererBackend{
    .mount = test_mnt,
};

const Label = ComponentTemplate{ // templates are defined in compile time
    .name = "Label",
    .parameters = EParameters{
        .parameters = .{EParameter{}},
    },
    .renderer = test_label_renderer, // Use GTK backend
};
pub fn main() !void {
    const allocator = std.heap.page_allocator;
    var parser = efus.Parser.init(allocator, "hello&banana");
    if (try parser.parse_compcall()) |comp| {
        print("parser {any}\n", .{comp});
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
