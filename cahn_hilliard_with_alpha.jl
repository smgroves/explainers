### A Pluto.jl notebook ###
# v0.19.27

using Markdown
using InteractiveUtils

# This Pluto notebook uses @bind for interactivity. When running this notebook outside of Pluto, the following 'mock version' of @bind gives bound variables a default value (instead of an error).
macro bind(def, element)
    quote
        local iv = try Base.loaded_modules[Base.PkgId(Base.UUID("6e696c72-6542-2067-7265-42206c756150"), "AbstractPlutoDingetjes")].Bonds.initial_value catch; b -> missing; end
        local el = $(esc(element))
        global $(esc(def)) = Core.applicable(Base.get, el) ? Base.get(el) : iv(el)
        el
    end
end

# ╔═╡ 1e0d077b-93d1-4eb9-a18b-c5634441783f
# ╠═╡ show_logs = false
begin
	import Pkg; Pkg.add("Plots")
	Pkg.add("PlutoUI")
	Pkg.add("LaTeXStrings")
	using Plots
	using PlutoUI
	using LaTeXStrings

end

# ╔═╡ 51c42871-4bb7-483d-b6d9-b88529dd3564
md"# Playing with Alpha Parameter in the Cahn Hilliard Equation"

# ╔═╡ fbc006da-ea95-46b8-84de-9022be4d280f
md"## Changing alpha.
Alpha is a parameter that affects the 'spinodal point' of the system. This determines whether the system preferentially goes to the -1 or +1 phase."

# ╔═╡ 119827b1-6415-44cb-8d16-4ee1cfe1f5d1
@bind alpha Slider(-1:0.05:1, default=0) 

# ╔═╡ a80a1194-95cd-49f1-8590-390cd5e31737
alpha

# ╔═╡ c6849a96-3d69-11ef-0933-0fd49936b533
# ╠═╡ skip_as_script = true
#=╠═╡
begin
	x = range(-1.5, 1.5, length=100)
	F = (1/4).*(x.^4).-(.5*x.^2)-(alpha/3).*(x.^3).+(alpha.*x)
	dF = (x.+1).*(x.-1).*(x.-alpha)
	ddF =3*(x.^2).-(2*alpha*x).-1
end
  ╠═╡ =#

# ╔═╡ a8f251bb-e55b-4821-b2f4-2164fd7ad59c
# plot(x,F, title = "Free Energy Functional", label = "F")


# ╔═╡ 6f57ebee-088d-4462-a850-e9853a3f2e41
function F_function(x, alpha)
	return 	(1/4)*(x^4)-(.5*x^2)-(alpha/3)*(x^3)+(alpha*x)
end

# ╔═╡ bde71c2a-60b2-48ba-aa2a-251971429bd9
function quadratic(a,b,c)
	discr = b^2 - 4*a*c
	roots = ( (-b + sqrt(discr))/(2a), (-b - sqrt(discr))/(2a) )
	return maximum(roots)
end

# ╔═╡ bcf114fc-fe6a-49b5-8ca0-be6ef9c06635
#=╠═╡
begin
	using Plots.PlotMeasures

	plot(x,[F,dF,ddF], title = "Free Energy Functional and Derivatives \n for alpha = $(alpha)", top_margin = 20px, label = ["F" L"$\frac{dF}{d\phi}$" L"$\frac{d^2F}{d\phi^2}$"],lw=[3 1 1],ls = [:solid :dash :dash],legend = :outertopright, size = (700,400))
	ylabel!("Free Energy Functional")
	xlabel!(L"$\phi$")
	ylims!(minimum(F), maximum(F))
	plot!(x, repeat([0], length(x)), color = "grey", label = "", lw = 2, ls = :dash)
	plot!([quadratic(3, -2*alpha, -1)], [0],seriestype=:scatter, label = "Spinodal point $(round(quadratic(3, -2*alpha, -1), sigdigits=3))")
	plot!([quadratic(3, -2*alpha, -1),quadratic(3, -2*alpha, -1)], [0,F_function(quadratic(3, -2*alpha, -1), alpha)], arrow = true,label="", color = "black", lw = 3)
	
end
  ╠═╡ =#

# ╔═╡ fdab8ce2-9230-43a4-9625-507f734fe39a


# ╔═╡ Cell order:
# ╠═51c42871-4bb7-483d-b6d9-b88529dd3564
# ╠═1e0d077b-93d1-4eb9-a18b-c5634441783f
# ╠═fbc006da-ea95-46b8-84de-9022be4d280f
# ╠═119827b1-6415-44cb-8d16-4ee1cfe1f5d1
# ╠═a80a1194-95cd-49f1-8590-390cd5e31737
# ╟─c6849a96-3d69-11ef-0933-0fd49936b533
# ╟─a8f251bb-e55b-4821-b2f4-2164fd7ad59c
# ╟─6f57ebee-088d-4462-a850-e9853a3f2e41
# ╟─bde71c2a-60b2-48ba-aa2a-251971429bd9
# ╠═bcf114fc-fe6a-49b5-8ca0-be6ef9c06635
# ╠═fdab8ce2-9230-43a4-9625-507f734fe39a
