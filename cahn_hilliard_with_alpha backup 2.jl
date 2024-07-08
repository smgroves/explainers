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
begin
	# import Pkg; Pkg.add("Plots")
	using Plots
	using PlutoUI
end

# ╔═╡ 51c42871-4bb7-483d-b6d9-b88529dd3564
md"# Playing with Alpha Parameter in the Cahn Hilliard Equation"

# ╔═╡ c6849a96-3d69-11ef-0933-0fd49936b533
begin
	@bind a Slider(-1:0.1:1, default=0) 
	x = range(-1.5, 1.5, length=100)
	F = (1/4).*(x.^4).-(.5*x.^2)-(a/3).*(x.^3).+(a.*x)
end

# ╔═╡ bcf114fc-fe6a-49b5-8ca0-be6ef9c06635
plot(x,F)

# ╔═╡ 78a9547b-945d-465d-b8f8-0f6942978c97
dF = (x.+1).*(x.-1).*(x.-a)

# ╔═╡ 082c1ba1-cc45-45c9-9f59-1dbd70aefef5
plot(x,dF)

# ╔═╡ Cell order:
# ╠═51c42871-4bb7-483d-b6d9-b88529dd3564
# ╠═1e0d077b-93d1-4eb9-a18b-c5634441783f
# ╠═c6849a96-3d69-11ef-0933-0fd49936b533
# ╠═bcf114fc-fe6a-49b5-8ca0-be6ef9c06635
# ╠═78a9547b-945d-465d-b8f8-0f6942978c97
# ╠═082c1ba1-cc45-45c9-9f59-1dbd70aefef5
